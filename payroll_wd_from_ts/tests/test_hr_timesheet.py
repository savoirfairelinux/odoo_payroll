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


class TestHrTimesheet(common.TransactionCase):
    def setUp(self):
        super(TestHrTimesheet, self).setUp()
        self.employee_model = self.env['hr.employee']
        self.user_model = self.env["res.users"]
        self.payslip_model = self.env["hr.payslip"]
        self.worked_days_model = self.env["hr.payslip.worked_days"]
        self.contract_model = self.env["hr.contract"]
        self.timesheet_model = self.env['hr_timesheet_sheet.sheet']
        self.account_model = self.env['account.analytic.account']
        self.wizard_model = self.env['hr.payslip.employees']
        self.run_model = self.env['hr.payslip.run']

        self.user_1 = self.user_model.create({
            'name': 'User 1',
            'login': 'test_user',
        })

        self.employee = self.employee_model.create({
            'name': 'Employee 1',
            'user_id': self.user_1.id,
        })

        self.contract = self.contract_model.create({
            'employee_id': self.employee.id,
            'name': 'Contract 1',
            'wage': 50000,
        })

        self.account = self.account_model.create({
            'name': 'Test timesheets',
            'uses_timesheets': True,
        })

        self.timesheet_1 = self.timesheet_model.create({
            'employee_id': self.employee.id,
            'date_from': '2015-02-15',
            'date_to': '2015-02-28',
            'timesheet_ids': [
                (0, 0, {
                    'user_id': self.user_1.id,
                    'unit_amount': 8,
                    'date': '2015-02-15',
                    'account_id': self.account.id,
                    'name': 'Test',
                    'is_timesheet': True,
                }),
                (0, 0, {
                    'user_id': self.user_1.id,
                    'unit_amount': 5,
                    'date': '2015-02-15',
                    'account_id': self.account.id,
                    'name': 'Test',
                    'is_timesheet': True,
                }),
                (0, 0, {
                    'user_id': self.user_1.id,
                    'unit_amount': 7,
                    'date': '2015-02-28',
                    'account_id': self.account.id,
                    'name': 'Test',
                    'is_timesheet': True,
                }),
            ],
        })

        self.timesheet_2 = self.timesheet_model.create({
            'employee_id': self.employee.id,
            'date_from': '2015-02-01',
            'date_to': '2015-02-14',
            'timesheet_ids': [
                (0, 0, {
                    'user_id': self.user_1.id,
                    'unit_amount': 8,
                    'date': '2015-02-01',
                    'account_id': self.account.id,
                    'name': 'Test',
                    'is_timesheet': True,
                }),
            ],
        })

        self.timesheet_1.write({'state': 'done'})
        self.timesheet_2.write({'state': 'done'})

    def test_worked_hours_total(self):
        self.payslip = self.payslip_model.create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'date_from': '2015-02-01',
            'date_to': '2015-02-28',
        })
        self.payslip.import_worked_days()
        total_hours = sum(
            wd.number_of_hours for wd in self.payslip.worked_days_line_ids)
        self.assertEqual(total_hours, 28)
        self.payslip.import_worked_days()
        total_hours = sum(
            wd.number_of_hours for wd in self.payslip.worked_days_line_ids)
        self.assertEqual(total_hours, 28)

    def test_payslip_run_wizard(self):
        self.run_1 = self.run_model.create({
            'name': 'Test',
            'date_start': '2015-02-01',
            'date_end': '2015-02-28',
        })

        self.wizard_model = self.wizard_model.with_context({
            'active_id': self.run_1.id,
        })
        wizard = self.wizard_model.create({
            'employee_ids': [(4, self.employee.id)],
        })
        wizard.compute_sheet()

        self.assertEqual(len(self.run_1.slip_ids), 1)
        payslip = self.run_1.slip_ids[0]

        total_hours = sum(
            wd.number_of_hours for wd in payslip.worked_days_line_ids)
        self.assertEqual(total_hours, 28)
