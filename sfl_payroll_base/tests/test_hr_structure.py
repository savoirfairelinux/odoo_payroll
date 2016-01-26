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

from openerp.tests import common


class TestHrStructureBase(common.TransactionCase):
    def setUp(self):
        super(TestHrStructureBase, self).setUp()

        self.structure_model = self.env['hr.payroll.structure']
        self.rule_model = self.env['hr.salary.rule']
        self.rule_category_model = self.env['hr.salary.rule.category']

        self.company_1 = self.env['res.company'].create({
            'name': 'Company 1',
            'currency_id': self.env.ref('base.CAD').id,
        })

        self.rule_category_1 = self.rule_category_model.create({
            'code': 'CAT_1',
            'name': 'Category 1',
        })

        self.rule_1 = self.rule_model.create({
            'name': 'Rule 1',
            'code': 'RULE_1',
            'amount_python_compute': "result = 500",
            'sequence': 10,
            'category_id': self.rule_category_1.id,
        })

        self.rule_2 = self.rule_model.create({
            'name': 'Rule 2',
            'code': 'RULE_2',
            'amount_python_compute': "result = RULE_1 - 400",
            'sequence': 20,
            'category_id': self.rule_category_1.id,
        })

        self.rule_3 = self.rule_model.create({
            'name': 'Rule 3',
            'code': 'RULE_3',
            'amount_python_compute': "result = RULE_1 - 200",
            'sequence': 20,
            'category_id': self.rule_category_1.id,
        })

        self.rule_4_1 = self.rule_model.create({
            'name': 'Rule 4.1',
            'code': 'RULE_4_1',
            'amount_python_compute': "result = RULE_1 + 1000",
            'sequence': 15,
            'category_id': self.rule_category_1.id,
        })

        self.rule_4_2 = self.rule_model.create({
            'name': 'Rule 4.2',
            'code': 'RULE_4_2',
            'amount_python_compute': "result = RULE_4_1 - 500",
            'sequence': 25,
            'category_id': self.rule_category_1.id,
        })

        self.structure_1 = self.structure_model.create({
            'name': 'Structure 1',
            'company_id': self.company_1.id,
            'rule_ids': [(6, 0, [
                self.rule_1.id,
            ])]
        })

        self.structure_2 = self.structure_model.create({
            'name': 'Structure 2',
            'company_id': self.company_1.id,
            'parent_id': self.structure_1.id,
            'rule_ids': [(6, 0, [
                self.rule_2.id,
            ])]
        })

        self.structure_3 = self.structure_model.create({
            'name': 'Structure 3',
            'company_id': self.company_1.id,
            'parent_id': self.structure_1.id,
            'rule_ids': [(6, 0, [
                self.rule_3.id,
            ])]
        })

        self.structure_4 = self.structure_model.create({
            'name': 'Structure 4',
            'company_id': self.company_1.id,
            'parent_id': self.structure_2.id,
            'rule_ids': [(6, 0, [
                self.rule_4_1.id,
                self.rule_4_2.id,
            ])]
        })


class TestHrStructure(TestHrStructureBase):
    def test_get_parent_structures(self):
        res = self.structure_1.get_parent_structures()
        self.assertEqual(self.structure_1, res)

        res = self.structure_2.get_parent_structures()
        self.assertEqual(self.structure_1 + self.structure_2, res)

        res = self.structure_4.get_parent_structures()
        self.assertEqual(
            self.structure_1 + self.structure_2 + self.structure_4, res)

    def test_get_all_rules(self):
        res = self.structure_4.get_all_rules()
        self.assertEqual(
            self.rule_1 + self.rule_2 + self.rule_4_1 + self.rule_4_2, res)

        structures = self.structure_1 + self.structure_4
        res = structures.get_all_rules()
        self.assertEqual(
            self.rule_1 + self.rule_2 + self.rule_4_1 + self.rule_4_2, res)
