# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2015 Savoir-faire Linux
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp import _, api, fields, models
from openerp.exceptions import ValidationError
from openerp.tools import float_is_zero, float_compare


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    journal_id = fields.Many2one(
        'account.journal',
        'Salary Journal',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True,
        default=lambda self: self.env.user.company_id.payroll_journal_id,
    )
    move_id = fields.Many2one(
        'account.move',
        'Accounting Entry',
        readonly=True,
        copy=False
    )

    @api.model
    def create(self, vals):
        journal_id = self.env.context.get('journal_id')
        if journal_id:
            vals.update({'journal_id': journal_id})
        return super(HrPayslip, self).create(vals)

    @api.multi
    def cancel_sheet(self):
        moves = self.mapped('move_id')
        moves_to_cancel = moves.filtered(lambda m: m.state == 'posted')

        moves_to_cancel.button_cancel()
        moves.unlink()

        return super(HrPayslip, self).cancel_sheet()

    @api.multi
    def process_sheet(self):
        move_pool = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Payroll')
        timenow = time.strftime('%Y-%m-%d')

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0

            employee_partner = slip.employee_id.address_home_id
            name = _('Payslip of %s') % (slip.employee_id.name)
            move_vals = {
                'narration': name,
                'date': timenow,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
            }
            for line in slip.details_by_salary_rule_category:
                amt = -line.amount if slip.credit_note else line.amount

                if float_is_zero(amt, precision_digits=precision):
                    continue

                rule = line.salary_rule_id
                register_partner = rule.register_id.partner_id

                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id
                analytic_account = rule.analytic_account_id

                if debit_account_id:

                    if (
                        rule.account_debit.internal_type not in
                        ['receivable', 'payable']
                    ):
                        partner_debit = self.env['res.partner']

                    elif register_partner:
                        partner_debit = register_partner

                    else:
                        partner_debit = employee_partner

                    debit_line = (0, 0, {
                        'name': line.name,
                        'date': timenow,
                        'partner_id': partner_debit.id,
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'debit': amt > 0.0 and amt or 0.0,
                        'credit': amt < 0.0 and -amt or 0.0,
                        'analytic_account_id': analytic_account.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += (
                        debit_line[2]['debit'] - debit_line[2]['credit']
                    )

                if credit_account_id:

                    if (
                        rule.account_credit.internal_type not in
                        ['receivable', 'payable']
                    ):
                        partner_credit = self.env['res.partner']

                    elif register_partner:
                        partner_credit = register_partner

                    else:
                        partner_credit = employee_partner

                    credit_line = (0, 0, {
                        'name': line.name,
                        'date': timenow,
                        'partner_id': partner_credit.id,
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'debit': amt < 0.0 and -amt or 0.0,
                        'credit': amt > 0.0 and amt or 0.0,
                        'analytic_account_id': analytic_account.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += (
                        credit_line[2]['credit'] - credit_line[2]['debit']
                    )

            if (
                float_compare(
                    credit_sum, debit_sum, precision_digits=precision) == -1
            ):
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise ValidationError(_(
                        'The Expense Journal "%s" has not properly configured '
                        'the Credit Account!') % slip.journal_id.name)
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': timenow,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif (
                float_compare(
                    debit_sum, credit_sum, precision_digits=precision) == -1
            ):
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise ValidationError(_(
                        'The Expense Journal "%s" has not properly configured '
                        'the Debit Account!') % slip.journal_id.name)
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': timenow,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)

            move_vals.update({'line_ids': line_ids})
            move = move_pool.create(move_vals)
            slip.write({'move_id': move.id})

        return super(HrPayslip, self).process_sheet()
