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


class TestSalaryRuleVariable(common.TransactionCase):
    def setUp(self):
        super(TestSalaryRuleVariable, self).setUp()
        self.employee_model = self.env['hr.employee']
        self.user_model = self.env["res.users"]
        self.payslip_model = self.env["hr.payslip"]
        self.contract_model = self.env["hr.contract"]
        self.variable_model = self.env["hr.salary.rule.variable"]
        self.rule_model = self.env["hr.salary.rule"]
        self.rule_category_model = self.env["hr.salary.rule.category"]
        self.structure_model = self.env["hr.payroll.structure"]

        # Create an employee
        self.employee = self.employee_model.create({
            'name': 'Employee 1',
        })

        # Get any existing category
        self.category = self.rule_category_model.search([], limit=1)[0]

        # Create salary rules
        self.rule = self.rule_model.create({
            'name': 'Test 1',
            'sequence': 1,
            'code': 'TEST_1',
            'category_id': self.category.id,
            'appears_on_payslip': True,
            'active': True,
            'amount_python_compute': """\
result = rule.variable(payslip.date_from)
""",
        })
        self.rule_2 = self.rule_model.create({
            'name': 'Test 2',
            'sequence': 2,
            'code': 'TEST_2',
            'category_id': self.category.id,
            'appears_on_payslip': True,
            'active': True,
            'amount_python_compute': """\
result = rule.variable(payslip.date_from)
""",
        })

        self.variables = {}
        # Create salary rule variables
        for variable in [
            (1, self.rule.id, '2014-01-01', '2014-01-31',
                'fixed', 500, False),
            (2, self.rule_2.id, '2014-01-01', '2014-01-31',
                'fixed', 75, False),
            # One record for testing with a python dict
            (3, self.rule.id, '2014-02-01', '2014-02-28',
                'python', False, {'TEST': 200}),
            # One record for testing with a python list
            (4, self.rule_2.id, '2014-02-01', '2014-02-28',
                'python', False, [300]),
        ]:
            self.variables[variable[0]] = self.variable_model.create({
                'salary_rule_id': variable[1],
                'date_from': variable[2],
                'date_to': variable[3],
                'variable_type': variable[4],
                'fixed_amount': variable[5],
                'python_code': variable[6],
            })

        # Create a structure
        self.structure = self.structure_model.create({
            'name': 'TEST',
            'parent_id': False,
            'code': 'TEST',
            'rule_ids': [(6, 0, [self.rule.id, self.rule_2.id])]
        })

        # Create a contract for the employee
        self.contract = self.contract_model.create({
            'employee_id': self.employee.id,
            'name': 'Contract 1',
            'wage': 50000,
            'struct_id': self.structure.id,
        })

        # Create a payslip
        self.payslip = self.payslip_model.create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'date_from': '2014-01-01',
            'date_to': '2014-01-31',
            'struct_id': self.structure.id,
        })

    def test_rule_variable(self):
        self.payslip.compute_sheet()
        self.payslip.refresh()

        # Check that every payslip lines were tested
        self.assertTrue(len(self.payslip.line_ids) == 2)

        for line in self.payslip.line_ids:
            if line.salary_rule_id == self.rule:
                self.assertTrue(line.amount == 500)

            elif line.salary_rule_id == self.rule_2:
                self.assertTrue(line.amount == 75)

            else:
                self.assertTrue(False)

    def test_rule_variable_with_python_code(self):
        self.payslip.write({
            'date_from': '2014-02-01',
            'date_to': '2014-02-28',
        })

        self.rule.write({
            'amount_python_compute': """\
variable = rule.variable(payslip.date_from)
result = variable['TEST']
"""
        })

        self.rule_2.write({
            'amount_python_compute': """\
variable = rule.variable(payslip.date_from)
result = variable[0]
"""
        })

        self.payslip.compute_sheet()
        self.payslip.refresh()

        # Check that every payslip lines were tested
        self.assertTrue(len(self.payslip.line_ids) == 2)

        for line in self.payslip.line_ids:
            if line.salary_rule_id == self.rule:
                self.assertTrue(line.amount == 200)

            elif line.salary_rule_id == self.rule_2:
                self.assertTrue(line.amount == 300)

            else:
                self.assertTrue(False)
