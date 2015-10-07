# -*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>)
#    Copyright (C) 2015 Savoir-faire Linux
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
from datetime import datetime
from dateutil import relativedelta

from openerp import api, fields, models, tools, _
from openerp.exceptions import ValidationError


class HrPayslip(models.Model):
    """Pay Slip"""

    _name = 'hr.payslip'
    _description = _(__doc__)

    struct_id = fields.Many2one(
        'hr.payroll.structure',
        'Structure',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    name = fields.Char(
        'Payslip Name',
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    number = fields.Char(
        'Reference',
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    employee_id = fields.Many2one(
        'hr.employee', 'Employee',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    date_from = fields.Date(
        'Date From',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    date_to = fields.Date(
        'Date To',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True,
        default=lambda self: fields.Date.context_today(self) +
        relativedelta(months=+1, day=1, days=-1),
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('verify', 'Waiting'),
            ('done', 'Done'),
            ('cancel', 'Rejected'),
        ], 'Status',
        select=True,
        readonly=True,
        copy=False,
        default='draft',
    )
    line_ids = fields.One2many(
        'hr.payslip.line',
        'slip_id',
        'Payslip Lines',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('appears_on_payslip', '=', True)],
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        default=lambda self: self.env.user.company_id.id,
    )
    worked_days_line_ids = fields.One2many(
        'hr.payslip.worked_days',
        'payslip_id',
        'Payslip Worked Days',
        copy=True,
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    input_line_ids = fields.One2many(
        'hr.payslip.input',
        'payslip_id',
        'Payslip Inputs',
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    paid = fields.Boolean(
        'Made Payment Order ? ',
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    note = fields.Text(
        'Internal Note',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    contract_id = fields.Many2one(
        'hr.contract',
        'Contract',
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    details_by_salary_rule_category = fields.One2many(
        'hr.payslip.line',
        'slip_id',
        'Detailed Payslip Lines',
        domain=[('appears_on_payslip', '=', True)],
    )
    credit_note = fields.Boolean(
        'Credit Note',
        help="Indicates this payslip has a refund of another",
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=False,
    )
    payslip_run_id = fields.Many2one(
        'hr.payslip.run',
        'Payslip Batches',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    payslip_line_count = fields.Integer(
        compute='_payslip_count',
        string='Payslip Computation Details',
    )

    @api.one
    def _payslip_count(self):
        self.payslip_line_count = len(self.details_by_salary_rule_category)

    @api.one
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if self.date_from > self.date_to:
            raise ValidationError(_(
                "Payslip 'Date From' must be before 'Date To'."
            ))

    @api.multi
    def cancel_sheet(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def process_sheet(self):
        return self.write({'paid': True, 'state': 'done'})

    @api.multi
    def hr_verify_sheet(self):
        self.compute_sheet()
        return self.write({'state': 'verify'})

    @api.multi
    def refund_sheet(self):
        for payslip in self:
            id_copy = self.copy(payslip.id, {
                'credit_note': True,
                'name': _('Refund: ') + payslip.name
            })
            self.signal_workflow([id_copy], 'hr_verify_sheet')
            self.signal_workflow([id_copy], 'process_sheet')

        return {
            'name': _("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % [id_copy],
            'context': {}
        }

    @api.multi
    def check_done(self):
        return True

    @api.multi
    def unlink(self):
        for payslip in self:
            if payslip.state not in ['draft', 'cancel']:
                raise ValidationError(
                    _('You cannot delete a payslip which is not draft '
                      'or cancelled!'))
        return super(HrPayslip, self).unlink()

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        :param employee: record set of employee
        :param date_from: date field
        :param date_to: date field
        :return: returns a record set of contracts for the given employee
        that need to be considered for the given dates
        """
        contract_obj = self.env['hr.contract']

        clause_1 = [
            '&',
            ('date_end', '<=', date_to),
            ('date_end', '>=', date_from)
        ]

        clause_2 = [
            '&',
            ('date_start', '<=', date_to),
            ('date_start', '>=', date_from)
        ]

        clause_3 = [
            '&',
            ('date_start', '<=', date_from),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', date_to)
        ]

        clause_final = [
            ('employee_id', '=', employee.id), '|', '|'
        ] + clause_1 + clause_2 + clause_3

        return contract_obj.search(clause_final)

    @api.multi
    def compute_sheet(self):
        sequence_obj = self.env['ir.sequence']

        for payslip in self:
            number = payslip.number or sequence_obj.get('salary.slip')

            payslip.details_by_salary_rule_category.unlink()

            lines = payslip.get_payslip_lines()
            self.write({
                'line_ids': lines,
                'number': number,
            })

    @api.multi
    def get_payslip_lines(self):
        self.ensure_one()

        result_dict = {}

        structures = self.contract_id.get_all_structures()
        sorted_rules = structures.get_all_rules().sorted('sequence')

        all_categories = sorted_rules.mapped('category_id')

        rules = {r.code: 0 for r in sorted_rules}
        categories = {c.code: 0 for c in all_categories}

        contract = self.contract_id
        employee = self.employee_id

        baselocaldict = {
            'categories': categories,
            'rules': rules,
            'payslip': self,
            'employee': employee,
            'contract': contract,
        }

        for rule in sorted_rules:

            localdict = baselocaldict.copy()
            localdict['result'] = None
            localdict['result_qty'] = 1.0
            localdict['result_rate'] = 100
            localdict['rule'] = rule

            if rule.satisfy_condition(localdict):

                amount = rule.compute_rule(localdict)
                category = rule.category_id

                previous_amount = rules[rule.code]
                if previous_amount:
                    categories[category.code] -= previous_amount

                rules[rule.code] = amount
                categories[category.code] += amount

                localdict[rule.code] = amount

                result_dict[rule.code] = {
                    'salary_rule_id': rule.id,
                    'contract_id': contract.id,
                    'category_id': category.id,
                    'amount': amount,
                    'employee_id': employee.id,
                }

        return [(0, 0, line) for line in result_dict.values()]

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.worked_days_line_ids.unlink()
        self.input_line_ids.unlink()
        self.details_by_salary_rule_category.unlink()

        self.contract_id = False
        self.struct_id = False
        self.name = ''

        if not (self.employee_id and self.date_from and self.date_to):
            return

        ttyme = datetime.fromtimestamp(
            time.mktime(time.strptime(self.date_from, "%Y-%m-%d")))

        employee = self.employee_id
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(ttyme.strftime('%B-%Y')))

        self.company_id = employee.company_id.id

        self.contract_id = self.get_contract(
            employee, self.date_from, self.date_to)

        self.struct_id = self.contract_id.struct_id

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        self.details_by_salary_rule_category.unlink()
