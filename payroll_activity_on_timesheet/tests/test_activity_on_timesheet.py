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

from openerp.tests import common


class test_activity_on_timesheet(common.TransactionCase):
    def setUp(self):
        super(test_activity_on_timesheet, self).setUp()
        self.employee_model = self.env['hr.employee']
        self.user_model = self.env["res.users"]
        self.contract_model = self.env["hr.contract"]
        self.job_model = self.env["hr.job"]
        self.activity_model = self.env["hr.activity"]
        self.account_model = self.env["account.analytic.account"]
        self.timesheet_model = self.env["account.analytic.line"]

        self.user = self.user_model.create({
            'name': 'User 1',
            'login': 'test',
            'password': 'test',
        })

        self.employee = self.employee_model.create({
            'name': 'Employee 1',
            'user_id': self.user.id,
        })

        self.job = self.job_model.create({'name': 'Job 1'})
        self.job_2 = self.job_model.create({'name': 'Job 2'})
        self.job_3 = self.job_model.create({'name': 'Job 3'})

        self.vac_activity_id = self.ref(
            'payroll_activity.activity_holiday_status_vacation')
        self.sl_activity_id = self.ref(
            'payroll_activity.activity_holiday_status_sl')

        self.contract = self.contract_model.create({
            'employee_id': self.employee.id,
            'name': 'Contract 1',
            'wage': 50000,
            'date_start': '2014-01-01',
            'contract_job_ids': [
                (0, 0, {
                    'job_id': self.job.id,
                    'is_main_job': False,
                }),
                (0, 0, {
                    'job_id': self.job_2.id,
                    'is_main_job': True,
                }),
            ],
        })

        self.account = self.account_model.create({
            'name': 'Account 1',
            'activity_type': 'job',
            'authorized_activity_ids': [(6, 0, [
                self.job_2.activity_ids.id,
                self.job_3.activity_ids.id,
            ])],
        })

    def test_01_on_change_activity_id_not_authorized(self):
        """
        Test on_change_activity_id when the given activity
        is not authorized on the analytic account
        """
        activity_id = self.job.activity_ids.id

        res = self.timesheet_model.onchange_account_id(
            self.account.id, user_id=self.user.id, activity_id=activity_id)

        self.assertNotEqual(res['value']['activity_id'], activity_id)

    def test_02_on_change_activity_id_authorized(self):
        """
        Test on_change_activity_id when the given activity
        is authorized on the analytic account
        """
        activity_id = self.job_2.activity_ids.id

        res = self.timesheet_model.onchange_account_id(
            self.account.id, user_id=self.user.id, activity_id=activity_id)

        self.assertEqual(res['value']['activity_id'], activity_id)

    def test_03_on_change_activity_id_no_activity(self):
        """
        Test on_change_activity_id when no activity is given in parameter
        """
        res = self.timesheet_model.onchange_account_id(
            self.account.id, user_id=self.user.id, activity_id=False)

        self.assertEqual(res['value']['activity_id'], False)

    def test_04_search_activities(self):
        """
        Test the method _search_activities_from_user on activity model.

        It returns a domain [('id', 'in', [...])] to filter activities on view
        """
        res = self.activity_model.with_context({
            'user_id': self.user.id, 'account_id': self.account.id
        })._search_activities_from_user()[0][2]

        activity_id = self.job.activity_ids.id
        activity_2_id = self.job_2.activity_ids.id
        activity_3_id = self.job_3.activity_ids.id

        self.assertIn(activity_2_id, res)

        # Job 1 is not in the account's authorized activities
        # Job 3 is not on the employee's contract
        self.assertNotIn(activity_id, res)
        self.assertNotIn(activity_3_id, res)

        # Leaves are not allowed for the analytic account
        self.assertNotIn(self.vac_activity_id, res)
        self.assertNotIn(self.sl_activity_id, res)

    def test_05_search_activities_leaves(self):
        """
        Test the method _search_activities_from_user with leave types
        authorized on the analytic account
        It returns a domain [('id', 'in', [...])] to filter activities on view
        """
        self.account.write({
            'activity_type': 'leave',
            'authorized_activity_ids': [(6, 0, [
                self.vac_activity_id
            ])]
        })

        res = self.activity_model.with_context({
            'user_id': self.user.id, 'account_id': self.account.id
        })._search_activities_from_user()[0][2]

        activity_id = self.job.activity_ids.id
        activity_2_id = self.job_2.activity_ids.id
        activity_3_id = self.job_3.activity_ids.id

        self.assertIn(self.vac_activity_id, res)

        # sl is not in the list of authorized activities
        self.assertNotIn(self.sl_activity_id, res)

        # Job positions are not allowed for the analytic account
        self.assertNotIn(activity_id, res)
        self.assertNotIn(activity_2_id, res)
        self.assertNotIn(activity_3_id, res)

    def test_06_search_activities_no_activity_on_account(self):
        """
        Test the method _search_activities_from_user on activity model
        with no authorized activities on the analytic account

        It returns a domain [('id', 'in', [...])] to filter activities on view
        """
        self.account.write({
            'activity_type': 'job',
            'authorized_activity_ids': [(6, 0, [])],
        })

        res = self.activity_model.with_context({
            'user_id': self.user.id, 'account_id': self.account.id
        })._search_activities_from_user()[0][2]

        activity_id = self.job.activity_ids.id
        activity_2_id = self.job_2.activity_ids.id
        activity_3_id = self.job_3.activity_ids.id

        self.assertIn(activity_id, res)
        self.assertIn(activity_2_id, res)

        # The job 3 does not appear on the employee's contract
        self.assertNotIn(activity_3_id, res)

        # Leaves are not allowed for the analytic account
        self.assertNotIn(self.vac_activity_id, res)
        self.assertNotIn(self.sl_activity_id, res)
