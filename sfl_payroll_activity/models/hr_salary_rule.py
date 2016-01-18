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

from openerp import fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    leave_activity_ids = fields.Many2many(
        'hr.activity',
        'hr_activity_salary_rule_rel',
        string='Related Leave Activities',
    )

    def _get_leave_activities(
        self, cr, uid, ids, context=None
    ):
        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, "Expected single record"

        rule = self.browse(cr, uid, ids[0], context=context)
        return rule.leave_activity_ids

    def reduce_leaves(
        self, cr, uid, ids, payslip, reduction,
        in_cash=False, context=None
    ):
        """
        When the leave hours computed in worked days are greater than the
        available hours from the employee's leave accrual, this method
        is called to reduce the worked days lines related to the leave type.

        :param in_cash: Whether to apply the reduction in cash or in hours
        """
        # To avoid integers as parameter to mess up with divisions
        reduction = float(reduction)

        activities = self._get_leave_activities(cr, uid, ids, context=context)

        worked_days = [
            wd for wd in payslip.leave_days_line_ids
            if wd.activity_id in activities
        ]

        worked_days.sort(key=lambda wd: wd.date)
        worked_days.reverse()

        for wd in worked_days:
            if reduction == 0:
                break

            current_reduction = (
                reduction / (wd.hourly_rate * wd.rate / 100)
                if in_cash else reduction
            )

            # Get the maximum of reduction of the current worked day
            current_reduction = min(
                wd.number_of_hours_allowed, current_reduction)
            current_reduction = max(current_reduction, 0)

            # Apply the reduction to the worked days line
            number_of_hours = wd.number_of_hours_allowed - current_reduction
            wd.write({'number_of_hours_allowed': number_of_hours})

            # substract the amount reduced before next iteration
            reduction -= (
                current_reduction * wd.hourly_rate * wd.rate / 100
                if in_cash else current_reduction
            )

    def sum_leaves_requested(
        self, cr, uid, ids, payslip, in_cash=False, context=None
    ):
        """
        Used in salary rules to sum leave hours from worked_days
        e.g. sum over the hours of vacation (leave_code == 'VAC')

        :param payslip: a payslip BrowsableObject or a browse_record
        :param in_cash: Whether to return an amount in cash of hours

        :return: the amount of allowance requested by the employee
        """
        activities = self._get_leave_activities(cr, uid, ids, context=context)

        worked_days = [
            wd for wd in payslip.leave_days_line_ids
            if wd.activity_id in activities
        ]

        if in_cash:
            return sum(wd.amount_requested for wd in worked_days)

        return sum(wd.number_of_hours for wd in worked_days)

    def sum_leaves_taken(
        self, cr, uid, ids, payslip, in_cash=False, context=None
    ):
        """
        Used in salary rules to sum leave hours from worked_days
        e.g. sum over the hours of vacation (leave_code == 'VAC')

        :param payslip: a payslip BrowsableObject or a browse_record
        :param in_cash: Whether to return an amount in cash of hours

        :return: the amount of allowance taken by the employee
        """
        activities = self._get_leave_activities(cr, uid, ids, context=context)

        worked_days = [
            wd for wd in payslip.leave_days_line_ids
            if wd.activity_id in activities
        ]

        if in_cash:
            return sum(wd.total for wd in worked_days)

        return sum(wd.number_of_hours for wd in worked_days)
