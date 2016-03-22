# -*- coding:utf-8 -*-#########################################################
#
#    Copyright (C) 2016 Savoir-faire Linux. All Rights Reserved.
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

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class HrReleve1Summary(models.Model):
    _inherit = 'hr.releve_1.summary'

    move_id = fields.Many2one(
        'account.move',
        'Accounting Entry',
        readonly=True,
    )

    @api.multi
    def button_confirm(self):
        super(HrReleve1Summary, self).button_confirm()
        self._cancel_account_move()
        self._create_account_move()

    @api.multi
    def button_cancel(self):
        super(HrReleve1Summary, self).button_cancel()
        self._cancel_account_move()

    @api.multi
    def _cancel_account_move(self):
        self.mapped('move_id').button_cancel()

    @api.multi
    def _create_account_move(self):

        revenu_quebec = self.env.ref(
            'payroll_quebec.partner_revenu_quebec')

        for summary in self:
            company = summary.company_id
            if not company.payroll_journal_id:
                raise ValidationError(
                    _("The payroll journal is not set for company %s.") %
                    company.name)

            rule_hsf = self.env.ref('payroll_quebec.rule_qc_hsf_er_c')

            hsf_debit = rule_hsf.account_debit
            hsf_credit = rule_hsf.account_credit

            if not hsf_debit or not hsf_credit:
                raise ValidationError(
                    _("You have not correctly set the "
                      "accounts for salary rule %s.") % rule_hsf.name)

            cnt_debit = company.qc_cnt_debit_account
            cnt_credit = company.qc_cnt_credit_account

            if not cnt_debit or not cnt_credit:
                raise ValidationError(
                    _("You have not correctly set the CNT "
                      "accounts for %s.")
                    % company.name)

            hsf_entry_name = _("HSF Contribution")
            cnt_entry_name = _("CNT Contribution")

            hsf_payable = summary.hsf_amount_payable
            cnt_payable = summary.cnt_amount_payable

            move_lines = [
                (0, 0, {
                    'name': hsf_entry_name,
                    'account_id': hsf_debit.id,
                    'debit': hsf_payable if hsf_payable > 0 else 0,
                    'credit': -hsf_payable if hsf_payable < 0 else 0,
                }),
                (0, 0, {
                    'name': hsf_entry_name,
                    'account_id': hsf_credit.id,
                    'partner_id': revenu_quebec.id,
                    'debit': -hsf_payable if hsf_payable < 0 else 0,
                    'credit': hsf_payable if hsf_payable > 0 else 0,
                }),
                (0, 0, {
                    'name': cnt_entry_name,
                    'account_id': cnt_debit.id,
                    'debit': cnt_payable if cnt_payable > 0 else 0,
                    'credit': -cnt_payable if cnt_payable < 0 else 0,
                }),
                (0, 0, {
                    'name': cnt_entry_name,
                    'account_id': cnt_credit.id,
                    'partner_id': revenu_quebec.id,
                    'debit': -cnt_payable if cnt_payable < 0 else 0,
                    'credit': cnt_payable if cnt_payable > 0 else 0,
                }),
            ]

            wsdrf_debit = company.qc_wsdrf_debit_account
            wsdrf_credit = company.qc_wsdrf_credit_account
            wsdrf_reported_account = company.qc_wsdrf_reported_account

            if summary.wsdrf_salaries:

                if (
                    not wsdrf_debit or not wsdrf_credit or
                    not wsdrf_reported_account
                ):
                    raise ValidationError(
                        _("You have not correctly set the WSDRF "
                          "accounts for %s.")
                        % company.name)

                wsdrf_entry_name = _("WSDRF Contribution")

                wsdrf_reported = (
                    summary.wsdrf_reported - summary.wsdrf_previous_reported)
                wsdrf_payable = summary.wsdrf_contribution
                wsdrf_expense = summary.wsdrf_contribution - wsdrf_reported

                move_lines += [
                    (0, 0, {
                        'name': wsdrf_entry_name,
                        'account_id': wsdrf_debit.id,
                        'debit': wsdrf_expense if wsdrf_expense > 0 else 0,
                        'credit': -wsdrf_expense if wsdrf_expense < 0 else 0,
                    }),
                    (0, 0, {
                        'name': wsdrf_entry_name,
                        'account_id': wsdrf_credit.id,
                        'partner_id': revenu_quebec.id,
                        'debit': -wsdrf_payable if wsdrf_payable < 0 else 0,
                        'credit': wsdrf_payable if wsdrf_payable > 0 else 0,
                    }),
                    (0, 0, {
                        'name': wsdrf_entry_name,
                        'account_id': wsdrf_reported_account.id,
                        'debit': wsdrf_reported if wsdrf_reported > 0 else 0,
                        'credit': -wsdrf_reported if wsdrf_reported < 0 else 0,
                    }),
                ]

            move = self.env['account.move'].create({
                'company_id': company.id,
                'journal_id': company.payroll_journal_id.id,
                'ref': _("Summary 1 - Year %s") % summary.year,
                'date': summary.date,
                'line_ids': move_lines,
            })

            summary.write({'move_id': move.id})
