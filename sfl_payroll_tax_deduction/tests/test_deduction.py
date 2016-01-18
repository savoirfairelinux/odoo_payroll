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


class TestDeduction(common.TransactionCase):
    def setUp(self):
        super(TestDeduction, self).setUp()
        self.employee_model = self.env['hr.employee']
        self.deduction_model = self.env['hr.deduction.category']
        self.jurisdiction_model = self.env['hr.deduction.jurisdiction']
        self.payslip_model = self.env["hr.payslip"]
        self.contract_model = self.env["hr.contract"]
        self.user_model = self.env["res.users"]
        self.rule_model = self.env['hr.salary.rule']
        self.rule_category_model = self.env["hr.salary.rule.category"]
        self.structure_model = self.env["hr.payroll.structure"]

        self.jurisdiction = self.jurisdiction_model.create({
            'name': 'Federal',
        })

        self.category = self.rule_category_model.search([], limit=1)

        self.rule = self.rule_model.create({
            'name': 'Test 1',
            'sequence': 1,
            'code': 'RULE_1',
            'category_id': self.category.id,
            'amount_python_compute': """
result = rule.sum_deductions(payslip)
"""
        })

        self.rule_2 = self.rule_model.create({
            'name': 'Test 2',
            'sequence': 1,
            'code': 'RULE_2',
            'category_id': self.category.id,
            'amount_python_compute': """
result = rule.sum_deductions(payslip)
"""
        })

        self.structure = self.structure_model.create({
            'name': 'TEST',
            'parent_id': False,
            'code': 'TEST',
            'rule_ids': [(6, 0, [self.rule.id, self.rule_2.id])]
        })

        self.deductions = [
            self.deduction_model.create({
                'name': 'Test',
                'jurisdiction_id': self.jurisdiction.id,
                'description': 'Test',
                'salary_rule_ids': [(6, 0, deduction[0])],
                'amount_type': deduction[1],
            })
            for deduction in [
                ([self.rule.id], 'annual'),
                ([self.rule.id, self.rule_2.id], 'each_pay'),
            ]
        ]

        self.employee = self.employee_model.create({
            'name': 'Employee 1',
            'deduction_ids': [
                (0, 0, {
                    'category_id': self.deductions[0].id,
                    'date_start': '2015-01-01',
                    'date_end': '2015-04-16',
                    'amount': 400,
                }),
                (0, 0, {
                    'category_id': self.deductions[0].id,
                    'date_start': '2015-05-15',
                    'date_end': '2015-07-31',
                    'amount': 600,
                }),
                (0, 0, {
                    'category_id': self.deductions[1].id,
                    'date_start': '2015-01-01',
                    'date_end': '2015-02-28',
                    'amount': 50,
                }),
                (0, 0, {
                    'category_id': self.deductions[1].id,
                    'date_start': '2015-01-01',
                    'date_end': '2015-12-31',
                    'amount': 60,
                }),
                (0, 0, {
                    'category_id': self.deductions[1].id,
                    'date_start': '2015-05-01',
                    'date_end': '2015-06-30',
                    'amount': 30,
                }),
            ],
        })

        self.contract = self.contract_model.create({
            'employee_id': self.employee.id,
            'name': 'Contract 1',
            'wage': 52000,
            'schedule_pay': 'monthly',
            'struct_id': self.structure.id,
        })

        self.payslip = self.payslip_model.create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'pays_per_year': 12,
            'date_from': '2015-02-01',
            'date_to': '2015-02-28',
            'date_payment': '2015-02-28',
            'struct_id': self.structure.id,
        })

    def compute_payslip(self):
        self.payslip.compute_sheet()

        return {
            line.code: line.amount
            for line in self.payslip.details_by_salary_rule_category
        }

    def test_sum_deductions(self):
        payslip = self.compute_payslip()

        self.assertEqual(round(payslip['RULE_1']), round(400 / 12 + 50 + 60))
        self.assertEqual(round(payslip['RULE_2']), 50 + 60)

    def test_sum_deductions_2(self):
        self.payslip.write({
            'date_from': '2015-04-16',
            'date_to': '2015-05-15',
            'date_payment': '2015-05-15',
        })

        payslip = self.compute_payslip()

        self.assertEqual(round(payslip['RULE_1']), 600 / 12 + 30 + 60)
        self.assertEqual(round(payslip['RULE_2']), 30 + 60)
