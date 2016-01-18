# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Savoir-faire Linux. All Rights Reserved.
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

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp


class HrPayslipWorkedDays(models.Model):

    _inherit = 'hr.payslip.worked_days'

    activity_id = fields.Many2one(
        'hr.activity',
        'Activity',
        required=True,
    )

    activity_type = fields.Selection(
        [
            ('leave', 'Leave'),
            ('job', 'Job'),
        ],
        'Activity Type',
        related='activity_id.activity_type',
        store=True,
    )

    number_of_hours_allowed = fields.Float(
        'Hours Allowed',
    )

    amount_requested = fields.Float(
        'Amount Requested',
        compute='_compute_amount_requested',
        store=True,
        digits_compute=dp.get_precision('Payroll'),
    )

    _order = 'date,activity_id'

    @api.model
    def create(self, vals):
        if 'number_of_hours_allowed' not in vals:
            vals['number_of_hours_allowed'] = vals.get('number_of_hours')
        return super(HrPayslipWorkedDays, self).create(vals)

    @api.one
    @api.depends(
        'hourly_rate', 'number_of_hours', 'rate', 'number_of_hours_allowed')
    def _compute_total(self):
        if self.activity_type != 'leave':
            super(HrPayslipWorkedDays, self)._compute_total()

        else:
            self.total = (
                self.hourly_rate *
                self.number_of_hours_allowed *
                self.rate
            ) / 100

    @api.one
    @api.depends('hourly_rate', 'number_of_hours', 'rate')
    def _compute_amount_requested(self):
        self.amount_requested = (
            self.hourly_rate * self.number_of_hours * self.rate) / 100
