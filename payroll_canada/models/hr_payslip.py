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

from datetime import datetime, timedelta

from openerp import api, fields, models

from_string = fields.Date.from_string
to_string = fields.Date.to_string
strftime = datetime.strftime


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    @api.multi
    def compute_sheet(self):
        self.check_employee_data()
        super(HrPayslip, self).compute_sheet()

    @api.multi
    def check_employee_data(self):
        """
        Check that no standard information is missing on the
        employee record. This prevents errors from being raised
        from salary rules.
        """
        self.mapped('employee_id').check_personal_info()

    @api.multi
    def get_4_weeks_of_gross(self, leave_date):
        """
        Get the gross salary of an employee within the 4 weeks that
        preceded a public holiday (leave_date).

        The end of the 4 week period depends on the employee's
        week start on contract.
        """
        self.ensure_one()

        # Get the number of days passed in the current week
        leave_day = from_string(leave_date)
        leave_weekday_num = int(strftime(leave_day, '%w'))

        week_start_day_num = int(
            self.contract_id.employee_id.company_id.week_start)

        if week_start_day_num > leave_weekday_num:
            week_start_day_num -= 7

        weekdays_passed = leave_weekday_num - week_start_day_num

        # Get the last day of the week that precedes the leave day
        period_end = (
            leave_day - timedelta(days=(weekdays_passed + 1))
        )

        # The periode start is 4 weeks before the period end
        period_start = period_end - timedelta(days=27)

        query = (
            """SELECT sum(
                case when p.credit_note then -wd.total else wd.total end)
            FROM hr_payslip_worked_days wd, hr_payslip p
            WHERE p.employee_id = %(employee_id)s
            AND p.company_id = %(company_id)s
            AND p.id = wd.payslip_id
            AND wd.date >= %(period_start)s
            AND wd.date <= %(period_end)s
            AND (p.state = 'done' or p.id = %(payslip_id)s)
            AND wd.activity_type = 'job'
            """
        )

        cr = self.env.cr

        cr.execute(query, {
            'period_start': period_start,
            'period_end': period_end,
            'company_id': self.company_id.id,
            'employee_id': self.employee_id.id,
            'payslip_id': self.id,
        })

        res = cr.fetchone()[0]

        return res or 0
