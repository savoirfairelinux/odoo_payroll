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

import subprocess
import codecs
import os

from openerp.osv import orm

from .test_hr_cra_t4 import TestHrCraT4Base

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
XML_SCHEMA_PATH = '%s/../data/cra_xml_schemas/layout-topologie.xsd' % \
    CURRENT_DIR


class TestHrCraT4Summary(TestHrCraT4Base):

    def test_check_contact_phone(self):
        """Test the _check_contact_phone returns False when
        the phone number format is not correct"""
        cr, uid, context = self.cr, self.uid, self.context

        for phone_number in [
            '88-8888', '888-888', '888', '8888888', 'aaa-aaaa', '',
        ]:
            self.assertRaises(
                orm.except_orm,
                self.summary_model.create, cr, uid, {
                    'year': 2014,
                    'company_id': self.company_id,
                    'proprietor_1_id': self.employee_id,
                    'contact_id': self.employee_id,
                    'contact_area_code': 888,
                    'contact_phone': phone_number,
                    'contact_email': 'test@test.com',
                    'contact_extension': 1234,
                    'sbmt_ref_id': '123456',
                }, context=context)

    def test_check_contact_phone_area_code(self):
        """Test the _check_contact_phone returns False when
        the area code format is not correct"""
        cr, uid, context = self.cr, self.uid, self.context

        for area_code in [
            1234, 12, 0,
        ]:
            self.assertRaises(
                orm.except_orm,
                self.summary_model.create, cr, uid, {
                    'year': 2014,
                    'company_id': self.company_id,
                    'proprietor_1_id': self.employee_id,
                    'contact_id': self.employee_id,
                    'contact_area_code': area_code,
                    'contact_phone': '888-8888',
                    'contact_email': 'test@test.com',
                    'contact_extension': 1234,
                    'sbmt_ref_id': '123456',
                }, context=context)

    def test_make_address_dict_res_partner(self):
        """Test the make_address_dict method computes without error and
        returns a dict when a partner is passed in parameter"""
        cr, uid, context = self.cr, self.uid, self.context

        address = self.partner_model.browse(
            cr, uid, self.address_id, context=context)

        res = self.summary_model.make_address_dict(
            cr, uid, address, context=context)

        self.assertIsInstance(res, dict)

    def test_make_address_dict_company(self):
        """Test the make_address_dict method computes without error and
        returns a dict when a company is passed in parameter"""
        cr, uid, context = self.cr, self.uid, self.context

        company = self.company_model.browse(
            cr, uid, self.company_id, context=context)

        res = self.summary_model.make_address_dict(
            cr, uid, company, context=context)

        self.assertIsInstance(res, dict)

    def test_make_t619_xml(self):
        """Test the make_t619_xml method computes without error and
        returns a dict"""
        cr, uid, context = self.cr, self.uid, self.context

        self.summary_id = self.summary_model.create(
            cr, uid, {
                'year': 2014,
                'company_id': self.company_id,
                'proprietor_1_id': self.employee_id,
                'contact_id': self.employee_id,
                'contact_area_code': 123,
                'contact_phone': '888-8888',
                'contact_email': 'test@test.com',
                'contact_extension': 1234,
                'sbmt_ref_id': '123456',
            }, context=context)

        summary = self.summary_model.browse(
            cr, uid, self.summary_id, context=context)

        self.summary_model.make_t619_xml(
            cr, uid, slip_return_xml='', summary=summary, context=context)

    def create_summary(self):
        cr, uid, context = self.cr, self.uid, self.context

        summary_id = self.summary_model.create(
            cr, uid, {
                'year': 2014,
                'company_id': self.company_id,
                'proprietor_1_id': self.employee_id,
                'contact_id': self.employee_id,
                'contact_area_code': 888,
                'contact_phone': '888-8888',
                'contact_email': 'test@test.com',
                'contact_extension': 1234,
                'sbmt_ref_id': '123456',
            }, context=context)

        return self.summary_model.browse(
            cr, uid, summary_id, context=context)

    def sum_payslip_amounts(self, code):
        return sum(slip[code] for slip in self.payslips)

    def set_t4_amount(self, slip, box_ref, amount):
        cr, uid, context = self.cr, self.uid, self.context
        box_id = self.data_model.get_object_reference(
            self.cr, self.uid, 'payroll_canada', box_ref)[1]

        box = self.box_model.browse(cr, uid, box_id, context=context)
        t4_amount = next(
            (a for a in slip.amount_ids if a.box_id == box), False)

        if t4_amount:
            t4_amount.unlink()

        slip.refresh()

        slip.write({
            'amount_ids': [
                (0, 0, {'amount': amount, 'box_id': box_id}),
            ],
        })

    def test_compute_t4_summary(self):
        """ Test that the T4 summary is computed properly
        """
        self.compute_payslips()

        summary = self.create_summary()
        summary.generate_slips()

        self.assertEqual(len(summary.t4_slip_ids), 2)

        slips = summary.t4_slip_ids
        for slip in slips:
            self.assertTrue(slip.computed)

        self.set_t4_amount(slips[0], 't4_box_padj_amt', 500)
        self.set_t4_amount(slips[1], 't4_box_padj_amt', 1500)

        # Add other amounts to a slip
        box_ids = self.box_model.search(
            self.cr, self.uid, [('is_other_amount', '=', True)], limit=2,
            context=self.context)

        slips[0].write({
            'amount_ids': [
                (0, 0, {'amount': 100, 'box_id': box_ids[0]}),
                (0, 0, {'amount': 200, 'box_id': box_ids[1]}),
            ],
        })

        # Generate slips a second time and verify that the
        # t4 reviously created won't be generated a second time
        summary.generate_slips()
        summary.refresh()

        self.assertEqual(len(summary.t4_slip_ids), 2)
        for slip in summary.t4_slip_ids:
            self.assertIn(slip, slips)

        self.payslips = [
            self.get_payslip_lines(slip_id) for slip_id
            in [
                self.payslip_ids[1], self.payslip_ids[2],
                self.payslip_ids[3]
            ]
        ]

        totals = {
            t.box_id.xml_tag: t.amount for t in summary.total_ids
        }

        self.assertEqual(
            round(totals['tot_empt_incamt']),
            round(self.sum_payslip_amounts('FIT_I_OTHER_WAGE')))

        self.assertEqual(
            round(totals['tot_empe_cpp_amt']),
            round(self.sum_payslip_amounts('CPP_EE_C')))

        self.assertEqual(
            round(totals['tot_empe_eip_amt']),
            round(self.sum_payslip_amounts('EI_EE_C')))

        self.assertEqual(
            round(totals['tot_rpp_cntrb_amt']),
            round(self.sum_payslip_amounts('RPP_EE_C')))

        self.assertEqual(
            round(totals['tot_itx_ddct_amt']),
            round(self.sum_payslip_amounts('FIT_T')))

        self.assertEqual(
            totals['tot_padj_amt'], 500 + 1500)

        self.assertEqual(
            round(totals['tot_empr_cpp_amt']),
            round(self.sum_payslip_amounts('CPP_ER_C')))

        self.assertEqual(
            round(totals['tot_empr_eip_amt']),
            round(self.sum_payslip_amounts('EI_ER_C')))

        summary.button_confirm_slips()
        summary.button_confirm()

        # Validate the produced transmission xml with the schema from the CRA
        filename = CURRENT_DIR + '/t4_summary_xml.xml'
        f = codecs.open(filename, 'w', 'UTF-8')
        f.write(summary.xml)
        f.close()

        subprocess.check_output([
            'xmllint', '--schema', XML_SCHEMA_PATH, filename])
