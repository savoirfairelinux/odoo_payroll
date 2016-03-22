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

from openerp.osv import orm
from openerp.addons.payroll_canada.tests.test_hr_cra_t4 import(
    TestHrCraT4Base)


class TestHrReleve1Base(TestHrCraT4Base):

    def setUp(self):
        super(TestHrReleve1Base, self).setUp()
        self.structure_model = self.registry("hr.payroll.structure")
        self.releve_1_model = self.registry("hr.releve_1")
        self.summary_model = self.registry("hr.releve_1.summary")
        self.fy_model = self.registry('hr.fiscalyear')
        self.period_model = self.registry('hr.period')
        self.box_model = self.registry('hr.releve_1.box')

        self.context = self.user_model.context_get(self.cr, self.uid)
        cr, uid, context = self.cr, self.uid, self.context

        # Create a company
        self.company_model.write(cr, uid, [self.company_id], {
            'rq_first_slip_number': 71997012,
            'rq_last_slip_number': 71997020,
            'rq_preparator_number': 'NP999999',
            'hsf_rate_ids': [(0, 0, {
                'date_from': '2014-01-01',
                'date_to': '2014-12-31',
                'rate': 2.0,
                'contribution_type': 'hsf',
            })],
        }, context=context)

        self.fy_id = self.fy_model.create(cr, uid, {
            'company_id': self.company_id,
            'date_start': '2014-01-01',
            'date_stop': '2014-12-31',
            'schedule_pay': 'monthly',
            'payment_day': '3',
            'name': 'Test',
        }, context=context)

        self.hr_period_ids = [
            self.period_model.create(cr, uid, {
                'fiscalyear_id': self.fy_id,
                'date_start': period[0],
                'date_stop': period[1],
                'date_payment': period[2],
                'schedule_pay': 'semi-monthly',
                'number': period[3],
                'name': 'test',
                'company_id': self.company_id,
            }, context=context) for period in [
                ('2014-01-01', '2014-01-31', '2014-02-03', 1),
                ('2014-02-01', '2014-02-28', '2014-03-03', 2),
                ('2014-03-01', '2014-03-31', '2014-04-03', 3),
            ]
        ]

        # Get the Quebec payroll structure
        self.structure_id = self.ref('payroll_quebec.hr_structure_qc')

        self.contract_model.write(cr, uid, [self.contract_id], {
            'struct_id': self.structure_id})

    def create_releve_1(self):
        cr, uid, context = self.cr, self.uid, self.context
        self.releve_1_id = self.releve_1_model.create(
            cr, uid, {
                'year': 2014,
                'employee_id': self.employee_id,
                'company_id': self.company_id,
            }, context=context)

    def check_releve_1_values(self):
        cr, uid, context = self.cr, self.uid, self.context
        slip = self.releve_1_model.browse(
            cr, uid, self.releve_1_id, context=context)

        payslip_1 = self.get_payslip_lines(self.payslip_ids[1])

        self.assertEqual(
            round(slip.get_amount('A'), 2),
            round(payslip_1['QIT_G'] * 2, 2))
        self.assertEqual(
            round(slip.get_amount('B'), 2),
            round(payslip_1['QPP_EE_C'] * 2, 2))
        self.assertEqual(
            round(slip.get_amount('C'), 2),
            round(payslip_1['EI_EE_C'] * 2, 2))
        self.assertEqual(
            round(slip.get_amount('D'), 2),
            round(payslip_1['RPP_EE_C'] * 2, 2))
        self.assertEqual(
            round(slip.get_amount('E'), 2),
            round(payslip_1['QIT_A'] * 2, 2))
        self.assertEqual(
            round(slip.get_amount('G'), 2),
            round(payslip_1['QPP_EE_MAXIE'] * 2, 2))
        self.assertEqual(
            round(slip.get_amount('H'), 2),
            round(payslip_1['PPIP_EE_C'] * 2, 2))
        self.assertEqual(
            round(slip.get_amount('I'), 2),
            round(payslip_1['PPIP_EE_MAXIE'] * 2, 2))


class TestHrReleve1(TestHrReleve1Base):

    def test_01_compute_amounts(self):
        """Test that the compute_amounts method on releve_1
        sums over the payslipsamounts properly"""
        cr, uid, context = self.cr, self.uid, self.context
        self.create_releve_1()

        self.compute_payslips()

        self.releve_1_model.compute_amounts(
            cr, uid, [self.releve_1_id], context=context)

        self.check_releve_1_values()

    def test_02_check_other_info_same_source(self):
        """Test _check_other_info raises an error when 2 other amounts
        have the same source"""
        cr, uid, context = self.cr, self.uid, self.context
        self.create_releve_1()

        releve_1 = self.releve_1_model.browse(
            cr, uid, self.releve_1_id, context=context)

        box_id = self.box_model.search(
            cr, uid, [('code', '=', 'A-1')], context=context)[0]

        self.assertRaises(
            orm.except_orm,
            releve_1.write, {
                'amount_ids': [
                    (0, 0, {'amount': 100, 'box_id': box_id}),
                    (0, 0, {'amount': 200, 'box_id': box_id}),
                ],
            }
        )

    def test_03_check_other_info_too_many_sources_1(self):
        cr, uid, context = self.cr, self.uid, self.context
        self.create_releve_1()

        releve_1 = self.releve_1_model.browse(
            cr, uid, self.releve_1_id, context=context)

        box_ids = self.box_model.search(
            cr, uid, [
                ('is_other_amount', '=', True),
                ('is_box_o_amount', '=', False),
            ], context=context)

        self.assertRaises(
            orm.except_orm,
            releve_1.write, {
                'amount_ids': [
                    (0, 0, {'amount': 100, 'box_id': box_ids[0]}),
                    (0, 0, {'amount': 200, 'box_id': box_ids[1]}),
                    (0, 0, {'amount': 300, 'box_id': box_ids[2]}),
                    (0, 0, {'amount': 400, 'box_id': box_ids[3]}),
                    (0, 0, {'amount': 500, 'box_id': box_ids[4]}),
                ],
            }
        )

    def test_04_check_other_info_too_many_sources_2(self):
        cr, uid, context = self.cr, self.uid, self.context
        self.create_releve_1()

        releve_1 = self.releve_1_model.browse(
            cr, uid, self.releve_1_id, context=context)

        box_ids = self.box_model.search(
            cr, uid, [
                ('is_other_amount', '=', True),
                ('is_box_o_amount', '=', False),
            ], context=context)
        box_o_ids = self.box_model.search(
            cr, uid, [
                ('is_other_amount', '=', True),
                ('is_box_o_amount', '=', True),
            ], context=context)

        self.assertRaises(
            orm.except_orm,
            releve_1.write, {
                'amount_ids': [
                    (5, 0),
                    (0, 0, {'amount': 100, 'box_id': box_ids[0]}),
                    (0, 0, {'amount': 200, 'box_id': box_ids[1]}),
                    (0, 0, {'amount': 300, 'box_id': box_ids[2]}),
                    (0, 0, {'amount': 400, 'box_id': box_o_ids[0]}),
                    (0, 0, {'amount': 500, 'box_id': box_o_ids[1]}),
                ],
            }
        )

    def test_05_check_other_info_too_many_sources_3(self):
        cr, uid, context = self.cr, self.uid, self.context
        self.create_releve_1()

        releve_1 = self.releve_1_model.browse(
            cr, uid, self.releve_1_id, context=context)

        box_ids = self.box_model.search(
            cr, uid, [
                ('is_other_amount', '=', True),
                ('is_box_o_amount', '=', False),
            ], context=context)
        box_o_ids = self.box_model.search(
            cr, uid, [
                ('is_other_amount', '=', True),
                ('is_box_o_amount', '=', True),
            ], context=context)

        # If there is only one box O amount, it should not be included
        # in the other amounts.
        releve_1.write({
            'amount_ids': [
                (0, 0, {'amount': 100, 'box_id': box_ids[0]}),
                (0, 0, {'amount': 200, 'box_id': box_ids[1]}),
                (0, 0, {'amount': 300, 'box_id': box_ids[2]}),
                (0, 0, {'amount': 400, 'box_id': box_ids[3]}),
                (0, 0, {'amount': 500, 'box_id': box_o_ids[0]}),
            ],
        })

        self.assertEqual(len(releve_1.other_amount_ids), 4)

    def test_06_make_dtmx_barcode(self):
        """Test make_dtmx_barcode method computes without error
        and creates a datamatrix string with the proper size"""
        cr, uid, context = self.cr, self.uid, self.context
        self.create_releve_1()

        self.releve_1_model.make_dtmx_barcode(
            cr, uid, [self.releve_1_id], context=context)

        releve_1 = self.releve_1_model.browse(
            cr, uid, self.releve_1_id, context=context)

        # In all cases, the bar code string must have 688 chars
        self.assertEqual(len(releve_1.dtmx_barcode_string), 688)
