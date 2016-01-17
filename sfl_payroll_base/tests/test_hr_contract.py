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

from .test_hr_structure import TestHrStructureBase


class TestHrContractBase(TestHrStructureBase):
    def setUp(self):
        super(TestHrContractBase, self).setUp()

        self.contract_model = self.env['hr.contract']

        self.user_1 = self.env['res.users'].create({
            'login': 'payroll_user_test_1',
            'name': 'Payroll User 1',
        })
        self.user_2 = self.env['res.users'].create({
            'login': 'payroll_user_test_2',
            'name': 'Payroll User 2',
        })
        self.employee_1 = self.env['hr.employee'].create({
            'user_id': self.user_1.id,
            'name': 'Employee 1',
        })
        self.employee_2 = self.env['hr.employee'].create({
            'user_id': self.user_2.id,
            'name': 'Employee 2',
        })
        self.contract_1 = self.contract_model.create({
            'name': 'Contract for Employee 1',
            'employee_id': self.employee_1.id,
            'struct_id': self.structure_4.id,
            'schedule_pay': 'weekly',
            'wage': 50000,
        })


class TestHrContract(TestHrContractBase):
    def test_get_all_structures(self):
        res = self.contract_1.get_all_structures()
        self.assertEqual(
            self.structure_1 + self.structure_2 + self.structure_4, res)
