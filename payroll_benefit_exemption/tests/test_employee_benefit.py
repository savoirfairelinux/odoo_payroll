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

from openerp.addons.payroll_employee_benefit.tests.\
    test_employee_benefit import TestEmployeeBenefitBase


class TestEmployeeBenefit(TestEmployeeBenefitBase):

    def setUp(self):

        super(TestEmployeeBenefit, self).setUp()
        self.exemption_model = self.env['hr.income.tax.exemption']

        self.exemption = self.exemption_model.create({
            'name': 'Test',
        })

        self.exemption_2 = self.exemption_model.create({
            'name': 'Test',
        })

        self.categories[0].write({
            'exemption_ids': [(4, self.exemption.id)]
        })

        self.categories[1].write({
            'exemption_ids': [(4, self.exemption_2.id)]
        })

    def remove_categories(self):
        self.rule.write({
            'employee_benefit_ids': [(5, 0)],
            'sum_all_benefits': True,
        })
        self.rule_2.write({
            'employee_benefit_ids': [(5, 0)],
            'sum_all_benefits': True,
        })

    def test_rule_with_categories(self):
        """ Test exemptions on rules linked to benefit categories
        No categories are exempted.
        """
        self.rule.write({'exemption_id': self.exemption.id})
        self.rule_2.write({'exemption_id': self.exemption_2.id})

        payslip = self.compute_payslip()
        self.assertEqual(payslip['RULE_1'], 20 + 600 / 12)
        self.assertEqual(payslip['RULE_2'], 720 / 12)

    def test_no_exemption(self):
        self.remove_categories()
        payslip = self.compute_payslip()
        self.assertEqual(payslip['RULE_1'], 20 + 600 / 12)
        self.assertEqual(payslip['RULE_2'], 40 + 720 / 12)

    def test_one_exemption(self):
        self.remove_categories()

        self.rule.write({'exemption_id': self.exemption.id})

        payslip = self.compute_payslip()
        self.assertEqual(payslip['RULE_1'], 600 / 12)
        self.assertEqual(payslip['RULE_2'], 40 + 720 / 12)

    def test_two_exemptions(self):
        self.remove_categories()

        self.rule.write({'exemption_id': self.exemption.id})
        self.rule_2.write({'exemption_id': self.exemption_2.id})

        payslip = self.compute_payslip()
        self.assertEqual(payslip['RULE_1'], 600 / 12)
        self.assertEqual(payslip['RULE_2'], 40)
