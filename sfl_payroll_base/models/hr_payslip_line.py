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

from openerp import fields, models, _
import openerp.addons.decimal_precision as dp


class HrPayslipLine(models.Model):
    """Payslip Line"""

    _name = 'hr.payslip.line'
    _description = _(__doc__)

    name = fields.Char(
        'Name',
        required=True,
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
    category_id = fields.Many2one(
        'hr.salary.rule.category',
        'Category',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        related='slip_id',
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        related='slip_id',
    )
    contract_id = fields.Many2one(
        'hr.contract',
        'Contract',
        related='slip_id',
    )
    appears_on_payslip = fields.Boolean(
        'Appears on Payslip',
        help="Used to display the salary rule on payslip.",
        default=True,
    )
