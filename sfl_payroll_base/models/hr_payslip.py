# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
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
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models, tools, _
from openerp.exceptions import ValidationError

to_string = fields.Date.to_string
from_string = fields.Date.from_string

PAYS_PER_YEAR = {
    'annually': 1,
    'semi-annually': 2,
    'quaterly': 4,
    'bi-monthly': 6,
    'monthly': 12,
    'semi-monthly': 24,
    'bi-weekly': 26,
    'weekly': 52,
    'daily': 365,
}


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
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    number = fields.Char(
        'Reference',
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
        default=lambda self: datetime.now(),
    )
    date_to = fields.Date(
        'Date To',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True,
        default=lambda self: datetime.now() +
        relativedelta(months=+1, days=-1),
    )
    date_payment = fields.Date(
        'Date of Payment',
        readonly=True,
        required=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: datetime.now() +
        relativedelta(months=+1, days=-1),
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
        domain=[
            ('appears_on_payslip', '=', True),
            ('amount', '!=', 0),
        ],
    )
    details_by_salary_rule_category = fields.One2many(
        'hr.payslip.line',
        'slip_id',
        'Detailed Payslip Lines',
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
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
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    input_line_ids = fields.One2many(
        'hr.payslip.input',
        'payslip_id',
        'Payslip Inputs',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    paid = fields.Boolean(
        'Made Payment Order ? ',
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
        readonly=True,
        states={'draft': [('readonly', False)]},
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
    pays_per_year = fields.Integer(
        compute='_get_pays_per_year',
        string='Number of pays per year',
        readonly=True,
        store=True,
        help="Field required to compute benefits based on an annual "
        "amount."
    )

    @api.depends('contract_id')
    def _get_pays_per_year(self):
        self.pays_per_year = PAYS_PER_YEAR.get(
            self.contract_id.schedule_pay, False)

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
            id_copy = payslip.copy({
                'credit_note': True,
                'name': _('Refund: ') + payslip.name
            })
            id_copy.signal_workflow('hr_verify_sheet')
            id_copy.signal_workflow('process_sheet')

        return {
            'name': _("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % [id_copy.id],
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
            number = payslip.number or sequence_obj.next_by_code('salary.slip')

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

        class BrowsableObject(object):
            def __init__(self, dict):
                self.dict = dict

            def __getattr__(self, attr):
                return (
                    attr in self.dict and
                    self.dict.__getitem__(attr) or 0.0
                )

        structures = self.contract_id.get_all_structures()
        all_rules = structures.get_all_rules().sorted(lambda r: r.sequence)
        rule_dict = {r.code: 0 for r in all_rules}
        rule_obj = BrowsableObject(rule_dict)

        all_categories = all_rules.mapped('category_id')
        category_dict = {c.code: 0 for c in all_categories}
        category_obj = BrowsableObject(category_dict)

        contract = self.contract_id
        employee = self.employee_id
        company = self.company_id

        baselocaldict = {
            'categories': category_obj,
            'rules': rule_obj,
            'payslip': self,
            'employee': employee,
            'company': company,
            'contract': contract,
        }

        for rule in all_rules:
            localdict = baselocaldict.copy()

            localdict['result'] = None
            localdict['rule'] = rule

            if rule.satisfy_condition(localdict):

                amount = rule.compute_rule(localdict)
                category = rule.category_id

                previous_amount = rule_dict[rule.code]

                if previous_amount:
                    category_dict[category.code] -= previous_amount

                rule_dict[rule.code] = amount
                baselocaldict[rule.code] = amount
                category_dict[category.code] += amount

                localdict[rule.code] = amount

                result_dict[rule.code] = {
                    'salary_rule_id': rule.id,
                    'category_id': category.id,
                    'amount': amount,
                    'sequence': rule.sequence,
                    'code': rule.code,
                    'name': rule.name,
                    'appears_on_payslip': rule.appears_on_payslip,
                    'amount_hours': amount,
                    'amount_type': rule.amount_type,
                    'register_id': rule.register_id.id,
                }

        return [(0, 0, line) for line in result_dict.values()]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.worked_days_line_ids = [(5, 0)]
        self.input_line_ids = [(5, 0)]
        self.details_by_salary_rule_category = [(5, 0)]
        self.line_ids = [(5, 0)]

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
    def onchange_contract_id(self):
        self.details_by_salary_rule_category = [(5, 0)]
        self.line_ids = [(5, 0)]

    @api.onchange('payslip_run_id')
    def onchange_payslip_run_id(self):
        payslip_run = self.payslip_run_id

        if not payslip_run:
            return

        self.onchange_employee_id()

        self.date_from = payslip_run.date_start
        self.date_to = payslip_run.date_end

    @api.multi
    def get_pays_since_beginning(self, pays_per_year):
        """
        Get the number of pay periods since the beginning of the year.
        """
        self.ensure_one()

        date_from = from_string(self.date_from)

        year_start = date(date_from.year, 1, 1)
        year_end = date(date_from.year, 12, 31)

        days_past = float((date_from - year_start).days)
        days_total = (year_end - year_start).days

        return round((days_past / days_total) * pays_per_year, 0) + 1
