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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.tests import common


class TestHrWorkedDays(common.TransactionCase):

    def setUp(self):
        super(TestHrWorkedDays, self).setUp()

        self.user_1 = self.env['res.users'].create({
            'login': 'payroll_user_test_1',
            'name': 'Payroll User 1',
        })
        self.employee_1 = self.env['hr.employee'].create({
            'user_id': self.user_1.id,
            'name': 'Employee 1',
        })
        self.contract_1 = self.env['hr.contract'].create({
            'name': 'Contract for Employee 1',
            'employee_id': self.employee_1.id,
            'schedule_pay': 'weekly',
            'wage': 50000,
        })

        self.date_from = datetime.now()
        self.date_to = self.date_from + relativedelta(weeks=1, days=-1)

        self.payslip_1 = self.env['hr.payslip'].create({
            'employee_id': self.employee_1.id,
            'contract_id': self.contract_1.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })

        self.paid_leave = self.env['hr.holidays.status'].create({
            'name': 'Paid Leave',
            'paid_leave': True,
        })
        self.paid_leave_activity = self.paid_leave.activity_ids[0]

        self.unpaid_leave = self.env['hr.holidays.status'].create({
            'name': 'Unpaid Leave',
            'paid_leave': False,
        })
        self.unpaid_leave_activity = self.unpaid_leave.activity_ids[0]

        self.job_1 = self.env['hr.job'].create({
            'name': 'Job 1',
        })
        self.job_activity = self.job_1.activity_ids[0]

    def test_01_create_worked_days(self):
        worked_days = self.env['hr.payslip.worked_days'].create({
            'payslip_id': self.payslip_1.id,
            'number_of_hours': 8,
            'hourly_rate': 30,
            'rate': 90,
            'date': self.date_from,
            'activity_id': self.job_activity.id,
        })

        self.assertEqual(len(self.payslip_1.worked_days_line_ids), 1)
        self.assertEqual(len(self.payslip_1.leave_days_line_ids), 0)
        self.assertEqual(worked_days.total, 8 * 30 * 0.9)

    def test_02_create_leave_days(self):
        worked_days = self.env['hr.payslip.worked_days'].create({
            'payslip_id': self.payslip_1.id,
            'number_of_hours': 8,
            'hourly_rate': 30,
            'rate': 90,
            'date': self.date_from,
            'activity_id': self.paid_leave_activity.id,
        })

        self.assertEqual(worked_days.number_of_hours_allowed, 8)
        worked_days.number_of_hours_allowed = 7

        self.assertEqual(len(self.payslip_1.worked_days_line_ids), 0)
        self.assertEqual(len(self.payslip_1.leave_days_line_ids), 1)
        self.assertEqual(worked_days.total, 7 * 30 * 0.9)
        self.assertEqual(worked_days.amount_requested, 8 * 30 * 0.9)

    def test_03_count_unpaid_leaves(self):
        for wd in [
            (7, self.paid_leave_activity.id),
            (9, self.unpaid_leave_activity.id),
            (11, self.unpaid_leave_activity.id),
            (12, self.job_activity.id),
        ]:
            self.env['hr.payslip.worked_days'].create({
                'payslip_id': self.payslip_1.id,
                'number_of_hours': wd[0],
                'hourly_rate': 30,
                'rate': 90,
                'date': self.date_from,
                'activity_id': wd[1],
            })

        res = self.payslip_1.count_unpaid_leaves()
        self.assertEqual(res, 9 + 11)

    def test_04_count_paid_worked_days(self):
        for wd in [
            (7, self.paid_leave_activity.id),
            (9, self.unpaid_leave_activity.id),
            (11, self.unpaid_leave_activity.id),
            (12, self.job_activity.id),
        ]:
            self.env['hr.payslip.worked_days'].create({
                'payslip_id': self.payslip_1.id,
                'number_of_hours': wd[0],
                'hourly_rate': 30,
                'rate': 90,
                'date': self.date_from,
                'activity_id': wd[1],
            })

        res = self.payslip_1.count_paid_worked_days(in_cash=False)
        self.assertEqual(res, 7 + 12)

        res = self.payslip_1.count_paid_worked_days(in_cash=True)
        self.assertEqual(res, (7 + 12) * 30 * 0.9)
