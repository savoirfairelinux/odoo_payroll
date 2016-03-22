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


class HrPayslipWorkedDays(models.Model):
    """Payslip Worked Days"""

    _name = 'hr.payslip.worked_days'
    _description = _(__doc__)

    payslip_id = fields.Many2one(
        'hr.payslip', 'Pay Slip',
        required=True,
        ondelete='cascade',
        index=True
    )
    date = fields.Date(
        'Date',
        default=fields.Date.today,
    )
    number_of_hours = fields.Float(
        'Number of Hours',
    )
    hourly_rate = fields.Float(
        'Hourly Rate',
        help="The employee's standard hourly rate for one hour of work. "
        "Example, 25 Euros per hour.",
        default=0,
        digits_compute=dp.get_precision('Payroll Rate'),
    )
    rate = fields.Float(
        'Rate (%)',
        help="The rate by which to multiply the standard hourly rate. "
        "Example, an overtime hour could be paid the standard rate "
        "multiplied by 150%.",
        digits_compute=dp.get_precision('Payroll Rate'),
        default=100,
    )
    total = fields.Float(
        'Total',
        compute='_compute_total',
        store=True,
        digits_compute=dp.get_precision('Payroll'),
    )

    @api.one
    @api.depends('hourly_rate', 'number_of_hours', 'rate')
    def _compute_total(self):
        self.total = (
            self.hourly_rate * self.number_of_hours * self.rate) / 100
