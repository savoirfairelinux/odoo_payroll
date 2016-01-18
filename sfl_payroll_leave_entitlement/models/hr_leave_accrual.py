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

import datetime
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models
from openerp.exceptions import ValidationError

from_string = fields.Date.from_string


class HrLeaveAccrual(models.Model):
    _inherit = 'hr.leave.accrual'

    @api.multi
    def sum_leaves_available(self, date, in_cash=False):
        """
        Sum the leave days that the employee is allowed to take
        for a given type of leave.

        If the leave uses holidays entitlements, the employee will be
        allowed to consume his leaves accruded before the date
        of entitlement.

        Example
        -------
        If the payslip is paid on March 15th 2015 and the day of
        entitlement is the 1rst of May, then the employee is allowed
        to consume his leaves accruded before the 1rst of May 2014.
        """
        self.ensure_one()

        leave_type = self.leave_type_id

        if not leave_type.uses_entitlement:
            return super(HrLeaveAccrual, self).sum_leaves_available(
                date, in_cash)

        date_slip = from_string(date)

        # Get the date of entitlement
        contract = self.employee_id.contract_id
        entitlement = contract.get_entitlement(leave_type)

        if not entitlement:
            raise ValidationError(
                "The %s entitlement for employee %s "
                "is not defined."
            )

        entitlement_date = datetime.date(
            date_slip.year,
            int(entitlement.month_start),
            entitlement.day_start)

        if entitlement_date > date_slip:
            entitlement_date -= relativedelta(years=1)

        current_year_end = entitlement_date + relativedelta(years=1)

        if in_cash:
            select_clause = """SELECT sum(amount)
            FROM hr_leave_accrual a, hr_leave_accrual_line_cash l
            """
        else:
            select_clause = """SELECT sum(amount)
            FROM hr_leave_accrual a, hr_leave_accrual_line_hours l
            """

        main_query = select_clause + """
            WHERE a.id = %(accrual_id)s
            AND l.accrual_id = a.id
            AND ((l.state = 'done') OR (l.source != 'payslip'))
            """

        # Leaves added and withdrawed before the entitlement date
        query_1 = main_query + """
            AND l.date < %(entitlement_date)s
            """

        # Leaves withdrawed in the current entitlement year
        query_2 = main_query + """
            AND l.date >= %(entitlement_date)s
            AND l.date < %(current_year_end)s
            AND (
                (l.is_refund AND l.amount > 0) or
                (not l.is_refund AND l.amount < 0)
            )
            """

        query_vals = {
            'entitlement_date': entitlement_date,
            'accrual_id': self.id,
            'current_year_end': current_year_end,
        }

        cr = self.env.cr

        cr.execute(query_1, query_vals)
        res_1 = cr.fetchone()[0] or 0

        cr.execute(query_2, query_vals)
        res_2 = cr.fetchone()[0] or 0

        return res_1 + res_2
