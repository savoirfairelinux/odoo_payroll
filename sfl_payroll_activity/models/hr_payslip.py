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

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    leave_days_line_ids = fields.One2many(
        'hr.payslip.worked_days',
        'payslip_id',
        domain=[('activity_type', '=', 'leave')],
        string="Leaves",
    )

    worked_days_line_ids = fields.One2many(
        domain=[('activity_type', '=', 'job')],
    )

    @api.multi
    def count_unpaid_leaves(self):
        """
        Count unpaid leaves in worked days for a given payslip
        """
        self.ensure_one()

        leave_days = self.leave_days_line_ids.filtered(
            lambda l: not l.activity_id.leave_id.paid_leave)

        return sum(l.number_of_hours for l in leave_days)

    @api.multi
    def count_paid_worked_days(self, in_cash=False):
        """
        Count paid worked days for a given payslip
        """
        self.ensure_one()

        worked_days = self.worked_days_line_ids

        worked_days += self.leave_days_line_ids.filtered(
            lambda l: l.activity_id.leave_id.paid_leave)

        if in_cash:
            return sum(wd.total for wd in worked_days)

        return sum(wd.number_of_hours for wd in worked_days)

    @api.constrains('leave_days_line_ids')
    def _check_max_leave_hours(self):
        """
        Check that the number of leave hours computed is lesser than
        the number of worked hours per pay period if the employee is paid
        by wage.
        """
        for payslip in self:
            if payslip.contract_id.salary_computation_method == 'wage':

                leave_hours = sum(
                    l.number_of_hours for l in payslip.leave_days_line_ids)

                limit = payslip.contract_id.worked_hours_per_pay_period

                if leave_hours > limit:
                    raise ValidationError(_(
                        "The leave hours taken by the employee "
                        "must be lower or equal to the number of worked "
                        "hours per pay period on the contract.",
                    ))
