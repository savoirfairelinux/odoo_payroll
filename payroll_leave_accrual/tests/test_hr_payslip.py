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


class TestLeaveAccrual(common.TransactionCase):

    def setUp(self):
        super(TestLeaveAccrual, self).setUp()

        self.employee_model = self.env['hr.employee']
        self.user_model = self.env["res.users"]
        self.contract_model = self.env["hr.contract"]
        self.payslip_model = self.env["hr.payslip"]
        self.rule_model = self.env["hr.salary.rule"]
        self.rule_category_model = self.env["hr.salary.rule.category"]
        self.structure_model = self.env["hr.payroll.structure"]
        self.leave_model = self.env['hr.holidays.status']

        self.category = self.rule_category_model.search([], limit=1)

        self.rule = self.rule_model.create({
            'name': 'Test 1',
            'sequence': 1,
            'code': 'RULE_1',
            'category_id': self.category.id,
            'amount_python_compute': "result = 300"
        })

        self.rule_2 = self.rule_model.create({
            'name': 'Test 2',
            'sequence': 2,
            'code': 'RULE_2',
            'category_id': self.category.id,
            'amount_python_compute': "result = 500"
        })

        self.rule_3 = self.rule_model.create({
            'name': 'Test 3',
            'sequence': 3,
            'code': 'RULE_3',
            'category_id': self.category.id,
            'amount_python_compute': "result = 700"
        })

        self.rule_4 = self.rule_model.create({
            'name': 'Test 4',
            'sequence': 4,
            'code': 'RULE_4',
            'category_id': self.category.id,
            'amount_python_compute': "result = 900"
        })

        self.leave_type = self.leave_model.create({
            'name': 'Test 1',
            'accrual_line_ids': [
                (0, 0, {
                    'salary_rule_id': self.rule.id,
                    'amount_type': 'cash',
                }),
                (0, 0, {
                    'salary_rule_id': self.rule_3.id,
                    'amount_type': 'cash',
                    'substract': True,
                }),
            ]
        })

        self.leave_type_2 = self.leave_model.create({
            'name': 'Test 2',
            'accrual_line_ids': [
                (0, 0, {
                    'salary_rule_id': self.rule_4.id,
                    'amount_type': 'cash',
                }),
            ]
        })

        self.leave_type_3 = self.leave_model.create({
            'name': 'Test 3',
        })

        self.structure = self.structure_model.create({
            'name': 'TEST',
            'parent_id': False,
            'code': 'TEST',
            'rule_ids': [(6, 0, [
                self.rule.id, self.rule_2.id,
                self.rule_3.id, self.rule_4.id,
            ])]
        })

        self.employee = self.employee_model.create(
            {'name': 'Employee 1'})

        self.contract = self.contract_model.create({
            'employee_id': self.employee.id,
            'name': 'Contract 1',
            'wage': 50000,
            'struct_id': self.structure.id,
        })

        self.payslip = self.payslip_model.create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'date_from': '2015-01-01',
            'date_to': '2015-01-31',
            'struct_id': self.structure.id,
        })

    def test_compute_payslip(self):

        self.payslip.compute_sheet()
        self.employee.refresh()

        self.assertEqual(len(self.employee.leave_accrual_ids), 2)

        accrual_1 = self.employee.get_leave_accrual(self.leave_type.id)
        accrual_2 = self.employee.get_leave_accrual(self.leave_type_2.id)
        self.assertEqual(accrual_1.total_cash, 0)
        self.assertEqual(accrual_2.total_cash, 0)

        self.payslip.process_sheet()
        accrual_1.refresh()
        accrual_2.refresh()
        self.assertEqual(accrual_1.total_cash, -400)
        self.assertEqual(accrual_2.total_cash, 900)

        self.payslip.cancel_sheet()
        accrual_1.refresh()
        accrual_2.refresh()
        self.assertEqual(accrual_1.total_cash, 0)
        self.assertEqual(accrual_2.total_cash, 0)
