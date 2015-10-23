# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
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

from openerp import api, fields, models


class HrPayslipWorkedDays(models.Model):

    _inherit = 'hr.payslip.worked_days'

    @api.depends('hourly_rate', 'number_of_hours', 'rate')
    def _compute_total(self):
        self.total = (
            self.hourly_rate * self.number_of_hours * self.rate) / 100

    hourly_rate = fields.Float(
        'Hourly Rate',
        help="The employee's standard hourly rate for one hour of work. "
        "Example, 25 Euros per hour.",
        default=0,
    )
    rate = fields.Float(
        'Rate (%)',
        help="The rate by which to multiply the standard hourly rate. "
        "Example, an overtime hour could be paid the standard rate "
        "multiplied by 150%.",
        default=100,
    )
    date_from = fields.Date(
        'Date From',
        default=fields.Date.today,
    )
    date_to = fields.Date(
        'Date To',
        default=fields.Date.today,
    )
    total = fields.Float(
        compute='_compute_total',
        store=True,
        string="Total",
        digits=(16, 2),
    )
