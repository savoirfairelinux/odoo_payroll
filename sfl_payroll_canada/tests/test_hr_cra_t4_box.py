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

from .test_hr_cra_t4 import TestHrCraT4Base


class TestHrCraT4Box(TestHrCraT4Base):

    def setUp(self):
        super(TestHrCraT4Box, self).setUp()
        cr, uid, context = self.cr, self.uid, self.context
        self.benefit_model = self.registry('hr.employee.benefit.category')
        self.benefit_rate_model = self.registry('hr.employee.benefit.rate')
        self.deduction_model = self.registry('hr.deduction.category')

        self.benefit_ids = [
            self.benefit_model.create(cr, uid, {
                'name': benefit[0],
                'description': 'Test',
                'code': 'Test',
            }, context=context)
            for benefit in [
                ('Benefit 1', ),
                ('Benefit 2', ),
            ]
        ]

        self.benefit_rate_ids = [
            self.benefit_rate_model.create(cr, uid, {
                'name': 'Test',
                'category_id': rate[0],
                'amount_type': 'each_pay',
            }, context=context)
            for rate in [
                (self.benefit_ids[0], ),
                (self.benefit_ids[1], ),
            ]
        ]

        self.box_benefit_ids = [
            self.box_model.create(cr, uid, {
                'name': 'Test',
                'xml_tag': box[0],
                'code': box[1],
                'type': 'benefit',
                'date_from': '2014-01-01',
                'is_other_amount': True,
                'benefit_line_ids': [(0, 0, {
                    'category_id': box[2],
                    'date_from': '2014-01-01',
                    'include_employer': box[3],
                    'include_employee': box[4],
                })]
            }, context=context) for box in [
                ('tag_1', 'code_1', self.benefit_ids[0], True, False),
                ('tag_2', 'code_2', self.benefit_ids[1], False, True),
            ]
        ]

        self.deduction_ids = [
            self.deduction_model.create(cr, uid, {
                'name': deduction[0],
                'description': 'Test',
                'jurisdiction_id': self.jurisdiction_id,
            }, context=context)
            for deduction in [
                ('Deduction 1', ),
                ('Deduction 2', ),
            ]
        ]

        self.box_deduction_ids = [
            self.box_model.create(cr, uid, {
                'name': 'Test',
                'xml_tag': box[0],
                'code': box[1],
                'type': 'deduction',
                'date_from': '2014-01-01',
                'is_other_amount': True,
                'deduction_line_ids': [(0, 0, {
                    'category_id': box[2],
                    'date_from': '2014-01-01',
                })]
            }, context=context) for box in [
                ('tag_3', 'code_3', self.deduction_ids[0]),
                ('tag_4', 'code_4', self.deduction_ids[1]),
            ]
        ]

    def create_more_boxes(self):
        cr, uid, context = self.cr, self.uid, self.context
        self.box_deduction_ids += [
            self.box_model.create(cr, uid, {
                'name': 'Test',
                'xml_tag': box[0],
                'code': box[1],
                'type': 'deduction',
                'date_from': '2014-01-01',
                'is_other_amount': True,
                'deduction_line_ids': [(0, 0, {
                    'category_id': box[2],
                    'date_from': '2014-01-01',
                })]
            }, context=context) for box in [
                ('tag_5', 'code_5', self.deduction_ids[1]),
                ('tag_6', 'code_6', self.deduction_ids[1]),
                ('tag_7', 'code_7', self.deduction_ids[1]),
                ('tag_8', 'code_8', self.deduction_ids[1]),
                ('tag_9', 'code_9', self.deduction_ids[1]),
                ('tag_10', 'code_10', self.deduction_ids[1]),
                ('tag_11', 'code_11', self.deduction_ids[1]),
                ('tag_12', 'code_12', self.deduction_ids[1]),
                ('tag_13', 'code_13', self.deduction_ids[1]),
                ('tag_14', 'code_14', self.deduction_ids[1]),
            ]
        ]

    def create_payslip(self, vals):
        cr, uid, context = self.cr, self.uid, self.context
        res = super(TestHrCraT4Box, self).create_payslip(vals)

        payslip = self.payslip_model.browse(cr, uid, res, context=context)

        payslip.write({
            'benefit_line_ids': [(0, 0, {
                'category_id': line[0],
                'employer_amount': line[1],
                'employee_amount': line[2],
            }) for line in [
                (self.benefit_ids[0], 300, 400),
                (self.benefit_ids[1], 550, 650),
            ]],
            'deduction_line_ids': [(0, 0, {
                'category_id': line[0],
                'amount': line[1],
            }) for line in [
                (self.deduction_ids[0], 700),
                (self.deduction_ids[1], 800),
            ]]
        })

        return res

    def atest_t4_get_amount(self):
        cr, uid, context = self.cr, self.uid, self.context

        self.create_t4_slip()

        self.compute_payslips()

        slip = self.t4_model.browse(cr, uid, self.t4_slip_id, context=context)

        slip.compute_amounts()
        slip.refresh()

        self.assertEqual(slip.get_amount('code_1'), 300 * 2)
        self.assertEqual(slip.get_amount('code_2'), 650 * 2)
        self.assertEqual(slip.get_amount('code_3'), 700 * 2)
        self.assertEqual(slip.get_amount('code_4'), 800 * 2)

        self.assertEqual(slip.get_amount(xml_tag='tag_1'), 300 * 2)
        self.assertEqual(slip.get_amount(xml_tag='tag_2'), 650 * 2)
        self.assertEqual(slip.get_amount(xml_tag='tag_3'), 700 * 2)
        self.assertEqual(slip.get_amount(xml_tag='tag_4'), 800 * 2)

    def test_compute_t4_with_many_other_amounts(self):
        cr, uid, context = self.cr, self.uid, self.context

        self.create_more_boxes()
        self.create_t4_slip()

        self.compute_payslips()

        slip = self.t4_model.browse(cr, uid, self.t4_slip_id, context=context)

        slip.compute_amounts()
        slip.refresh()

        # 14 other amounts, 6 other amounts per T4
        self.assertEqual(len(slip.child_ids), 2)

        other_amounts = []

        for child in slip.child_ids:
            # Check that the child slip has no standard amount
            std_amounts = [
                a for a in child.amount_ids if not a.is_other_amount
            ]

            self.assertEqual(sum(a.amount for a in std_amounts), 0)
            # Get the child's other amounts
            other_amounts += [
                a for a in child.amount_ids if a.is_other_amount
            ]

        self.assertEqual(len(other_amounts), 8)
