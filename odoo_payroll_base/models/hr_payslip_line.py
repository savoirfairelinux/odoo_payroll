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

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


class HrPayslipLine(models.Model):
    """Payslip Line"""

    _name = 'hr.payslip.line'
    _inherit = 'hr.salary.rule'
    _description = _(__doc__)

    slip_id = fields.Many2one(
        'hr.payslip',
        'Pay Slip',
        required=True,
        ondelete='cascade'
    )
    salary_rule_id = fields.Many2one(
        'hr.salary.rule',
        'Rule',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        required=True,
    )
    rate = fields.Float(
        'Rate (%)',
        digits_compute=dp.get_precision('Payroll Rate'),
        default=100.0,
    )
    amount = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Payroll'),
    )
    quantity = fields.Float(
        'Quantity',
        digits_compute=dp.get_precision('Payroll'),
        default=1.0,
    )
    total = fields.Float(
        compute='_compute_total',
        type='float',
        string='Total',
        digits_compute=dp.get_precision('Payroll'),
        store=True,
    )

    @api.one
    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        self.total = float(self.quantity) * self.amount * self.rate / 100
