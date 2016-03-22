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
from datetime import datetime


class TestHrHolidaysStatus(common.TransactionCase):

    def setUp(self):
        super(TestHrHolidaysStatus, self).setUp()

        self.company_model = self.env['res.company']
        self.employee_model = self.env['hr.employee']
        self.user_model = self.env["res.users"]
        self.leave_model = self.env['hr.holidays.status']
        self.request_model = self.env['hr.holidays']

        self.company = self.company_model.create({
            'name': 'Company Test',
            'currency_id': self.env.ref('base.CAD').id,
            'holidays_hours_per_day': 7.5,
        })

        self.user_1 = self.user_model.create({
            'login': 'user_1',
            'name': 'User Test 1',
            'email': 'test@localhost',
            'company_id': self.company.id,
            'company_ids': [(4, self.company.id)],
            'groups_id': [(4, self.ref('base.group_hr_user'))],
        })

        self.user_2 = self.user_model.create({
            'login': 'user_2',
            'name': 'User Test 2',
            'email': 'test@localhost',
            'company_id': self.company.id,
            'company_ids': [(4, self.company.id)],
        })

        self.user_3 = self.user_model.create({
            'login': 'user_3',
            'name': 'User Test 3',
            'company_id': self.company.id,
            'company_ids': [(4, self.company.id)],
        })

        self.manager = self.employee_model.create({
            'name': 'Manager',
            'user_id': self.user_1.id,
            'company_id': self.company.id,
        })

        self.employee = self.employee_model.create({
            'name': 'Employee 1',
            'parent_id': self.manager.id,
            'user_id': self.user_2.id,
            'company_id': self.company.id,
        })

        self.employee_2 = self.employee_model.create({
            'name': 'Employee 2',
            'user_id': self.user_3.id,
            'company_id': self.company.id,
        })

        self.leave_type = self.leave_model.create({
            'name': 'Test',
            'limit': True,
            'increase_accrual_on_allocation': True,
        })

        self.request = self.request_model.create({
            'employee_id': self.employee.id,
            'holiday_status_id': self.leave_type.id,
            'date_from': '2015-01-01',
            'date_to': '2015-01-03',
            'number_of_days_temp': 3,
            'type': 'add',
            'holiday_type': 'employee',
        })

    def test_holidays_validate(self):
        """
        Validate the leave request as the manager
        """
        self.request.sudo(self.user_1.id).holidays_validate()

        accrual = self.employee.get_leave_accrual(self.leave_type.id)
        self.assertEqual(accrual.total_hours, 22.5)

    def test_leave_accrual_access_rights(self):
        """
        Test the access rigths to models hr.leave.accrual
        and hr.leave.accrual.line
        """
        accrual = self.employee.get_leave_accrual(self.leave_type.id)
        accrual.write({
            'line_ids': [(0, 0, {
                'name': 'Test',
                'amount_cash': 100,
                'date': datetime.now(),
            })],
        })

        self.assertRaises(
            Exception,
            accrual.sudo(self.user_3.id).check_access_rule, 'read')

        self.assertRaises(
            Exception,
            accrual.sudo(self.user_2.id).check_access_rights, 'write')

        accrual.sudo(self.user_1.id).check_access_rule('read')
        self.assertTrue(
            accrual.sudo(self.user_1.id).check_access_rights('read'))

        # The manager can not access the leave accruals of the employee 2
        # because he is not the employee's manager
        accrual_2 = self.employee_2.get_leave_accrual(self.leave_type.id)

        self.assertRaises(
            Exception,
            accrual_2.sudo(self.user_1.id).check_access_rule, 'read')

        self.user_1.write({
            'groups_id': [(4, self.ref('base.group_hr_manager'))]})

        for operation in ['read', 'write', 'create', 'unlink']:
            accrual_2.sudo(self.user_1.id).check_access_rule(operation)
            self.assertTrue(
                accrual_2.sudo(self.user_1.id).check_access_rights(operation))
