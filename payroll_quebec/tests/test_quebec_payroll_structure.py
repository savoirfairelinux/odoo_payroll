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

from openerp.addons.payroll_canada.tests.test_hr_cra_t4 import (
    TestPayrollStructureBase)


class TestQuebecPayrollStructure(TestPayrollStructureBase):

    def setUp(self):
        super(TestQuebecPayrollStructure, self).setUp()

        cr, uid, context = self.cr, self.uid, self.context

        self.employee_id = self.employee_model.create(cr, uid, {
            'firstname': 'john',
            'lastname': 'doe',
            'address_id': self.address_id,
            'address_home_id': self.address_id,
            'sin': 901505802,
            'qc_additional_source_deduction': 50,
            'deduction_ids': [
                (0, 0, {
                    'category_id': self.ref(ded[0]),
                    'date_start': '2014-01-01',
                    'date_end': '2014-12-31',
                    'amount_type': 'each_pay',
                    'amount': ded[1],
                }) for ded in [
                    ('payroll_canada.rrsp', 15),
                    ('payroll_quebec.qitf', 16),
                    ('payroll_quebec.qitj', 17),
                    ('payroll_quebec.qitj1', 18),
                    ('payroll_quebec.qitk1', 988),
                    ('payroll_quebec.qite', 1040),
                    ('payroll_quebec.qitq', 21),
                    ('payroll_quebec.qitq1', 22),
                ]
            ]
        }, context=context)

        # Get the canadian payroll structure
        self.structure_id = self.structure_model.search(
            cr, uid, [('code', '=', 'QC')], context=context)[0]

        self.benefit_rate_ids = [
            self.benefit_rate_model.create(cr, uid, {
                'name': 'Test',
                'category_id': self.get_benefit_id(rate[0]),
                'amount_type': 'percent_gross',
            }, context=context)
            for rate in [
                ('rpp', ),
                ('prpp', ),
                ('vrsp', ),
            ]
        ]

        self.benefit_line_ids = [
            self.benefit_rate_line_model.create(cr, uid, {
                'parent_id': line[0],
                'employee_amount': line[1],
                'employer_amount': line[2],
                'date_start': line[3],
                'date_end': line[4],
            }, context=context)
            for line in [
                (self.benefit_rate_ids[0], 0.1, 0.2,
                    '2014-01-01', '2014-12-31'),
                (self.benefit_rate_ids[1], 0.4, 0.8,
                    '2014-01-01', '2014-12-31'),
                (self.benefit_rate_ids[2], 0.9, 1.8,
                    '2014-01-01', '2014-12-31'),
            ]
        ]

        # Create a contract
        self.contract_id = self.contract_model.create(
            cr, uid, {
                'employee_id': self.employee_id,
                'name': 'Contract 1',
                'wage': 52000,
                'salary_computation_method': 'hourly',
                'schedule_pay': 'weekly',
                'struct_id': self.structure_id,
                'worked_hours_per_pay_period': 40,
                'weeks_of_vacation': 4,
                'benefit_line_ids': [
                    (0, 0, {
                        'category_id': self.get_benefit_id(ben[0]),
                        'date_start': '2014-01-01',
                        'date_end': '2014-12-31',
                        'rate_id': ben[1],
                    }) for ben in [
                        ('rpp', self.benefit_rate_ids[0]),
                        ('prpp', self.benefit_rate_ids[1]),
                        ('vrsp', self.benefit_rate_ids[2]),
                    ]
                ],
                'contract_job_ids': [
                    (0, 0, {
                        'job_id': self.job_id,
                        'is_main_job': True,
                        'hourly_rate_class_id': self.rate_class_id,
                    }),
                ],
            }, context=context,
        )

        self.payslip_vals = {
            'company_id': self.company_id,
            'employee_id': self.employee_id,
            'contract_id': self.contract_id,
            'date_from': '2014-01-01',
            'date_to': '2014-01-07',
            'date_payment': '2014-01-07',
            'struct_id': self.structure_id,
        }

    def test_create_payslip_low_wage(self):
        self.payslip_1_id = self.create_payslip(self.payslip_vals)
        self.create_worked_days([
            # (date, activity_id, nb_hours, hourly_rate)
            ('2014-01-01', self.job_activity_id, 40, 22),
        ])

        self.create_inputs([
            (self.ref('payslip_input_bonus'), 30),
        ])

        payslip = self.compute_payslip()

        p = 52
        self.assertEqual(payslip['GROSSP'], 40 * 22)
        self.assertEqual(
            round(payslip['QIT_G'], 2),
            round(payslip['GROSSP'] * (1 + 0.008 + 0.018), 2))

        pension_rate = 0.001 + 0.004 + 0.008 + 0.009 + 0.018

        self.assertEqual(payslip['QIT_H'], round(1110.0 / p, 2))

        self.assertEqual(
            round(payslip['QIT_I']), round((
                payslip['QIT_G'] -
                pension_rate * payslip['GROSSP'] - 15 - 16 - 17 - 18 -
                payslip['QIT_H']) * p
            ))

        self.assertEqual(
            round(payslip['QIT_R']), round(payslip['QIT_I'] + 16 * p))

        # QIT_R is between 40390 and 42390
        self.assertEqual(
            round(payslip['QIT_Z'] * p),
            round(100 + (payslip['QIT_R'] - 40390) * 0.05))

        self.assertEqual(
            round(payslip['QIT_Y']),
            round(
                payslip['QIT_I'] * 0.16 -
                (21 * 0.15 + 22 * 0.25) * p -
                988 * 0.15 - 1040 * 0.20
            ))

        self.assertEqual(
            round(payslip['QIT_A']),
            round(
                payslip['QIT_Y'] / p + 50 + payslip['QIT_Z'] +
                payslip['QIT_Z_OTHER_WAGE'] + 30 * 0.16))

        # Check the federal tax rules overriden by quebec structure
        self.assertEqual(
            round(payslip['FIT_K2'] / 52),
            round(
                payslip['EI_EE_C'] + payslip['QPP_EE_C'] +
                payslip['PPIP_EE_C']))

        fit_t1 = payslip['FIT_T1']

        self.assertEqual(
            round(fit_t1),
            round(payslip['FIT_T3'] - 0.165 * payslip['FIT_T3']))

    def test_create_payslip_higher_wage(self):
        """
        The same test as above but with a wage over 80k
        so the tax bracket is different
        """
        self.payslip_1_id = self.create_payslip(self.payslip_vals)
        self.create_worked_days([
            # (date, activity_id, nb_hours, hourly_rate)
            ('2014-01-01', self.job_activity_id, 40, 40),
        ])

        self.create_inputs([
            (self.ref('payslip_input_bonus'), 300),
            (self.ref('payslip_input_retro_pay'), 700)
        ])

        payslip = self.compute_payslip()

        p = 52
        self.assertEqual(payslip['GROSSP'], 40 * 40)
        self.assertEqual(
            round(payslip['QIT_G'], 2),
            round(payslip['GROSSP'] * (1 + 0.008 + 0.018), 2))

        self.assertEqual(payslip['QIT_H'], round(1110.0 / p, 2))

        pension_rate = 0.001 + 0.004 + 0.008 + 0.009 + 0.018
        self.assertEqual(
            round(payslip['QIT_I']), round(
                payslip['QIT_G'] * p -
                (pension_rate * payslip['GROSSP'] + 15 + 16 + 17 + 18) * p -
                payslip['QIT_H'] * p))

        self.assertEqual(
            round(payslip['QIT_R']), round(payslip['QIT_I'] + 16 * p))

        self.assertEqual(payslip['QIT_Z'], round(200.0 / p, 2))

        self.assertEqual(
            round(payslip['QIT_Y']),
            round(
                payslip['QIT_I'] * 0.20 - 1659 -
                (21 * 0.15 + 22 * 0.25) * p -
                988 * 0.15 - 1040 * 0.20
            ))

        self.assertEqual(
            round(payslip['QIT_A']),
            round(
                payslip['QIT_Y'] / p + 50 + payslip['QIT_Z'] +
                payslip['QIT_Z_OTHER_WAGE'] + 1000 * 0.20))

        # Check the federal tax rules overriden by quebec structure
        self.assertEqual(
            round(payslip['FIT_K2']),
            round(743.58 + 385.71 + 2535.75))

        fit_t1 = payslip['FIT_T1']

        self.assertEqual(
            round(fit_t1),
            round(payslip['FIT_T3'] - 0.165 * payslip['FIT_T3']))

    def test_create_payslip_end_of_year(self):
        """
        Test the salary rules, when the payslip is at the end
        of the year.
        Need to compute 4 payslips (1 payslip each 3 months)
        and check the results for the last one
        """
        cr, uid, context = self.cr, self.uid, self.context

        # Create 4 payslips
        payslips = {
            ps[0]: self.create_payslip({
                'employee_id': self.employee_id,
                'contract_id': self.contract_id,
                'date_from': ps[1],
                'date_to': ps[2],
                'date_payment': ps[2],
                'struct_id': self.structure_id,
            })
            for ps in [
                (1, '2014-01-01', '2014-03-31'),
                (2, '2014-04-01', '2014-06-30'),
                (3, '2014-07-01', '2014-09-30'),
                (4, '2014-10-01', '2014-12-31'),
            ]
        }

        self.contract_model.write(
            cr, uid, [self.contract_id], {
                'employee_id': self.employee_id,
                'name': 'Contract 1',
                'wage': 83200,
                'schedule_pay': 'quarterly',
                'struct_id': self.structure_id,
                'worked_hours_per_pay_period': 520,
                'weeks_of_vacation': 4,
            }, context=context)
        # Create the worked_days records
        for wd in [
            # (date_from, date_to, activity_id, nb_hours, hourly_rate)
            ('2014-01-01', self.job_activity_id, 520, 45, 1),
            ('2014-04-01', self.job_activity_id, 520, 45, 2),
            ('2014-07-01', self.job_activity_id, 520, 45, 3),
            ('2014-10-01', self.job_activity_id, 520, 45, 4),
        ]:
            self.worked_days_model.create(
                cr, uid, {
                    'date': wd[0],
                    'activity_id': wd[1],
                    'number_of_hours': wd[2],
                    'hourly_rate': wd[3],
                    'payslip_id': payslips[wd[4]],
                }, context=context)

        # Add a bonus and a retroactive pay increase payment to payslip 2
        for input_line in [
            (self.ref('payslip_input_bonus'), 30),
            (self.ref('payslip_input_retro_pay'), 70)
        ]:
            self.input_model.create(
                cr, uid, {
                    'name': 'Test',
                    'payslip_id': payslips[2],
                    'category_id': input_line[0],
                    'amount': input_line[1],
                })

        for payslip in payslips.values():
            self.payslip_model.compute_sheet(
                cr, uid, [payslip],
                context=context)
            self.payslip_model.write(
                cr, uid, [payslip], {
                    'state': 'done',
                }, context=context)

        payslip2 = self.get_payslip_lines(payslips[2])
        payslip4 = self.get_payslip_lines(payslips[4])

        self.assertEqual(payslip4['GROSSP'], 520 * 45)

        taxable_earning = payslip4['GROSSP'] * (1 + 0.008 + 0.018) + 30 + 70

        # Employment insurance
        self.assertEqual(payslip4['EI_EE_C'], 0)
        self.assertEqual(
            round(payslip2['EI_EE_C']),
            round(taxable_earning * 0.0153))

        self.assertEqual(payslip4['EI_ER_C'], 0)
        self.assertEqual(
            round(payslip2['EI_ER_C']),
            round(payslip2['EI_EE_C'] * 1.4))

        # Provincial parental insurance plan
        self.assertEqual(payslip4['PPIP_EE_C'], 0)
        self.assertEqual(
            round(payslip2['PPIP_EE_C']),
            round(taxable_earning * 0.00559))

        self.assertEqual(payslip4['PPIP_ER_C'], 0)
        self.assertEqual(
            round(payslip2['PPIP_ER_C']),
            round(taxable_earning * 0.00782))

        # Quebec pension plan
        self.assertEqual(payslip4['QPP_EE_C'], 0)
        self.assertEqual(
            round(payslip2['QPP_EE_C']),
            round((taxable_earning - 3500 / 4) * 0.05175))

        self.assertEqual(payslip4['QPP_ER_C'], 0)
        self.assertEqual(payslip2['QPP_ER_C'], payslip2['QPP_EE_C'])

        # Canada pension plan
        self.assertEqual(payslip2['CPP_EE_MAXIE'], 0)

        # Canada income tax
        self.assertEqual(
            round(payslip4['FIT_K2']), round(743.58 + 2535.75 + 385.71))
