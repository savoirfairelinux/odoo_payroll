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

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


class HrPayslipLine(models.Model):
    """Payslip Line"""

    _name = 'hr.payslip.line'
    _description = _(__doc__)

    _order = 'sequence'

    name = fields.Char(
        'Name',
        required=True,
        translate=True,
    )
    slip_id = fields.Many2one(
        'hr.payslip',
        'Pay Slip',
        required=True,
        ondelete='cascade',
        index=True,
    )
    salary_rule_id = fields.Many2one(
        'hr.salary.rule',
        'Rule',
        required=True,
    )
    sequence = fields.Integer(
        'Sequence',
        required=True,
    )
    code = fields.Char(
        'Code',
        required=True,
    )
    amount = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Payroll'),
    )
    amount_hours = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Payroll Hours'),
    )
    total = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Payroll'),
        compute='_compute_total',
        store=True,
        help='Amount displayed for contribution registers.'
    )
    amount_type = fields.Selection(
        [
            ('cash', 'Monetary'),
            ('number', 'Number'),
        ],
        type='char',
        string='Amount Type',
        help="Used to compute the decimal precision on the amount."
    )
    category_id = fields.Many2one(
        'hr.salary.rule.category',
        'Category',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        related='slip_id.employee_id',
        store=True,
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        related='slip_id.company_id',
        store=True,
    )
    contract_id = fields.Many2one(
        'hr.contract',
        'Contract',
        related='slip_id.contract_id',
        store=True,
    )
    appears_on_payslip = fields.Boolean(
        'Appears on Payslip',
        help="Used to display the salary rule on payslip.",
        default=True,
    )
    register_id = fields.Many2one(
        'hr.contribution.register',
        'Contribution Register',
        help="Eventual third party involved in the salary payment of "
        "the employees.",
    )

    @api.one
    @api.depends('amount')
    def _compute_total(self):
        total = self.amount

        if self.slip_id.credit_note:
            total *= -1

        self.total = total
