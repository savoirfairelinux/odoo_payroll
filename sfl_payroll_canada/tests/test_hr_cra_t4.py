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

from .test_payroll_structure import TestPayrollStructureBase


class TestHrCraT4Base(TestPayrollStructureBase):
    def setUp(self):
        super(TestHrCraT4Base, self).setUp()
        self.job_model = self.registry("hr.job")
        self.t4_model = self.registry("hr.cra.t4")
        self.summary_model = self.registry("hr.cra.t4.summary")
        self.box_model = self.registry("hr.cra.t4.box")

        cr, uid, context = self.cr, self.uid, self.context

        self.address_home_id = self.partner_model.create(
            cr, uid, {
                'name': 'test',
                'street': 'test',
                'street2': 'test',
                'city': 'Québec',
                'zip': 'P1P1P1',
                'country_id': self.canada_id,
                'state_id': self.state_id,
            }, context=context)

        # Create an employee
        self.employee_model.write(
            cr, uid, [self.employee_id], {
                'address_home_id': self.address_home_id,
                'address_id': self.address_home_id,
                'sin': 684242680,
            }, context=context)

        self.employee_2_id = self.employee_model.create(
            cr, uid, {
                'name': 'Employee 2',
                'firstname': 'Jane',
                'lastname': 'Doe',
                'company_id': self.company_id,
                'address_home_id': self.address_home_id,
                'address_id': self.address_home_id,
                'sin': 624842680,
            }, context=context)

        self.contract_2_id = self.contract_model.create(cr, uid, {
            'employee_id': self.employee_2_id,
            'name': 'Contract 2',
            'wage': 80000,
            'schedule_pay': 'weekly',
            'worked_hours_per_pay_period': 40,
            'weeks_of_vacation': 4,
            'salary_computation_method': 'yearly',
            'contract_job_ids': [
                (0, 0, {
                    'job_id': self.job_id,
                    'is_main_job': True,
                }),
            ],
        }, context=context)

    def compute_payslips(self):
        cr, uid, context = self.cr, self.uid, self.context

        # Create a payslip
        self.payslip_ids = {
            payslip[0]: self.create_payslip({
                'company_id': self.company_id,
                'employee_id': payslip[3],
                'contract_id': self.contract_id,
                'date_from': payslip[1],
                'date_to': payslip[2],
                'date_payment': payslip[2],
                'struct_id': self.structure_id,
            }) for payslip in [
                (1, '2014-01-01', '2014-01-31',
                    self.employee_id, self.contract_id),
                (2, '2014-06-01', '2014-06-30',
                    self.employee_2_id, self.contract_2_id),
                (3, '2014-12-01', '2014-12-31',
                    self.employee_id, self.contract_id),

                # payslip that will be excluded from
                # the computation because the dates don't match
                (4, '2015-01-01', '2015-01-31',
                    self.employee_id, self.contract_id),
            ]
        }

        # Create the worked_days records
        for wd in [
            # (date_from, payslip)
            ('2014-01-01', 1),
            ('2014-06-01', 2),
            ('2014-12-01', 3),
            ('2015-01-01', 4),
        ]:
            self.worked_days_model.create(
                cr, uid, {
                    'date': wd[0],
                    'activity_id': self.job_activity_id,
                    'number_of_hours': 160,
                    'hourly_rate': 50,
                    'payslip_id': self.payslip_ids[wd[1]],
                }, context=context)

        for payslip_id in self.payslip_ids.values():
            self.payslip_model.compute_sheet(
                cr, uid, [payslip_id], context=context)

            self.payslip_model.write(
                cr, uid, [payslip_id], {'state': 'done'},
                context=context)

    def create_t4_slip(self):
        cr, uid, context = self.cr, self.uid, self.context
        self.t4_slip_id = self.t4_model.create(
            cr, uid, {
                'year': 2014,
                'employee_id': self.employee_id,
                'empt_prov_cd': 'AB',
            }, context=context)

    def get_t4(self, t4_slip_id):
        cr, uid, context = self.cr, self.uid, self.context
        t4 = self.t4_model.browse(cr, uid, t4_slip_id, context=context)

        return {
            a.box_id.xml_tag: a.amount for a in t4.amount_ids
        }

    def check_t4_slip_values(self):
        t4 = self.get_t4(self.t4_slip_id)

        payslip_1 = self.get_payslip_lines(self.payslip_ids[1])

        self.assertEqual(
            t4['empt_incamt'], round(payslip_1['FIT_I_OTHER_WAGE'] * 2, 2))
        self.assertEqual(
            t4['cpp_cntrb_amt'], round(payslip_1['CPP_EE_C'] * 2, 2))
        self.assertEqual(
            t4['empe_eip_amt'], round(payslip_1['EI_EE_C'] * 2, 2))
        self.assertEqual(t4['itx_ddct_amt'], round(payslip_1['FIT_T'] * 2, 2))
        self.assertEqual(
            t4['ei_insu_ern_amt'], round(payslip_1['EI_EE_MAXIE'] * 2, 2))
        self.assertEqual(
            t4['cpp_qpp_ern_amt'], round(payslip_1['CPP_EE_MAXIE'] * 2, 2))
        self.assertEqual(
            t4['empr_cpp_amt'], round(payslip_1['CPP_ER_C'] * 2, 2))
        self.assertEqual(
            t4['empr_eip_amt'], round(payslip_1['EI_ER_C'] * 2, 2))
        self.assertEqual(
            t4['rpp_cntrb_amt'], round(payslip_1['RPP_EE_C'] * 2, 2))

        for label in [
            'FIT_I_OTHER_WAGE', 'CPP_EE_C', 'EI_EE_C', 'FIT_T',
            'EI_EE_MAXIE', 'CPP_EE_MAXIE', 'CPP_ER_C', 'EI_ER_C', 'RPP_EE_C'
        ]:
            self.assertNotEqual(payslip_1[label], 0)


class TestHrCraT4(TestHrCraT4Base):

    def test_compute_amounts(self):
        """Test that the compute_amounts method on T4 sums over the payslips
        amounts properly"""
        cr, uid, context = self.cr, self.uid, self.context

        self.create_t4_slip()

        self.compute_payslips()

        self.t4_model.compute_amounts(
            cr, uid, [self.t4_slip_id], context=context)

        self.check_t4_slip_values()

    def test_check_other_amounts_same_source(self):
        """Test _check_other_amounts raises an error when 2 other amounts
        have the same source"""
        cr, uid, context = self.cr, self.uid, self.context

        self.create_t4_slip()
        t4 = self.t4_model.browse(cr, uid, self.t4_slip_id, context=context)

        box_ids = self.box_model.search(
            cr, uid, [('code', '=', '30')], limit=1, context=context)

        self.assertRaises(
            orm.except_orm,
            t4.write, {
                'amount_ids': [
                    (0, 0, {'amount': 100, 'box_id': box_ids[0]}),
                    (0, 0, {'amount': 200, 'box_id': box_ids[0]}),
                ],
            }
        )

    def test_check_other_amounts_too_many_sources(self):
        """Test _check_other_amounts raises an error when 7 other amounts
        are computed
        """
        cr, uid, context = self.cr, self.uid, self.context

        self.create_t4_slip()
        t4 = self.t4_model.browse(cr, uid, self.t4_slip_id, context=context)

        box_ids = self.box_model.search(
            cr, uid, [('is_other_amount', '=', True)], context=context)

        self.assertRaises(
            orm.except_orm,
            t4.write, {
                'amount_ids': [
                    (0, 0, {'amount': 100, 'box_id': box_ids[0]}),
                    (0, 0, {'amount': 200, 'box_id': box_ids[1]}),
                    (0, 0, {'amount': 300, 'box_id': box_ids[2]}),
                    (0, 0, {'amount': 400, 'box_id': box_ids[3]}),
                    (0, 0, {'amount': 500, 'box_id': box_ids[4]}),
                    (0, 0, {'amount': 600, 'box_id': box_ids[5]}),
                    (0, 0, {'amount': 700, 'box_id': box_ids[6]}),
                ],
            }
        )
