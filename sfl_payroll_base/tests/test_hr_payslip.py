# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015 Savoir-faire Linux
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

from .test_hr_contract import TestHrContractBase


class TestHrPayslipBase(TestHrContractBase):
    def setUp(self):
        super(TestHrPayslipBase, self).setUp()

        self.date_from = datetime.now()
        self.date_to = self.date_from + relativedelta(weeks=1, days=-1)
        self.date_payment = self.date_from + relativedelta(weeks=2, days=-1)

        self.payslip_1 = self.env['hr.payslip'].create({
            'employee_id': self.employee_1.id,
            'contract_id': self.contract_1.id,
            'struct_id': self.structure_4.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'date_payment': self.date_payment,
        })


class TestHrPayslip(TestHrPayslipBase):

    def create_other_contracts(self):
        vals = {
            'name': 'Contract for Employee 1',
            'employee_id': self.employee_1.id,
            'struct_id': self.structure_4.id,
            'schedule_pay': 'weekly',
            'wage': 50000,
        }

        vals_2 = vals.copy()
        vals_3 = vals.copy()
        vals_4 = vals.copy()
        vals_5 = vals.copy()

        vals_2.update({
            'date_start': self.date_from - relativedelta(months=6),
            'date_end': self.date_from - relativedelta(days=1),
        })
        self.contract_2 = self.contract_model.create(vals_2)

        vals_3.update({
            'date_start': self.date_to + relativedelta(days=1),
            'date_end': self.date_to + relativedelta(months=6),
        })
        self.contract_3 = self.contract_model.create(vals_3)

        vals_4.update({
            'date_start': self.date_from,
            'date_end': self.date_to,
        })
        self.contract_4 = self.contract_model.create(vals_4)

        vals_5.update({
            'date_start': self.date_from,
            'date_end': self.date_to,
            'employee_id': self.employee_2.id,
        })
        self.contract_5 = self.contract_model.create(vals_5)

    def test_get_contract(self):
        self.create_other_contracts()

        res = self.env['hr.payslip'].get_contract(
            self.employee_1, self.date_from, self.date_to)

        self.assertIn(self.contract_1, res)
        self.assertNotIn(self.contract_2, res)
        self.assertNotIn(self.contract_3, res)
        self.assertIn(self.contract_4, res)
        self.assertNotIn(self.contract_5, res)

    def test_compute(self):
        self.payslip_1.compute_sheet()

        lines = {
            l.code: l.amount for l in
            self.payslip_1.details_by_salary_rule_category
        }

        self.assertEqual(lines['RULE_1'], 500)
        self.assertEqual(lines['RULE_2'], 100)
        self.assertEqual(lines['RULE_4_1'], 1500)
        self.assertEqual(lines['RULE_4_2'], 1000)
