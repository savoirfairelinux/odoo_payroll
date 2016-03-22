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

from .test_hr_payslip import TestPayslipBase


class TestPayrollStructureBase(TestPayslipBase):
    def get_payslip_lines(self, payslip_id):
        """
        Get a dict of payslip lines
        """
        payslip = self.payslip_model.browse(
            self.cr, self.uid, payslip_id, context=self.context)

        return {
            line.code: line.amount
            for line in payslip.details_by_salary_rule_category
        }

    def get_deduction_id(self, ref, module='payroll_canada'):
        """
        Gets a deduction category id
        """
        return self.data_model.get_object_reference(
            self.cr, self.uid, module, ref)[1]

    def get_benefit_id(self, ref, module='payroll_canada'):
        """
        Gets an employee benefit category id
        """
        return self.data_model.get_object_reference(
            self.cr, self.uid, module, ref)[1]

    def setUp(self):
        super(TestPayrollStructureBase, self).setUp()
        self.data_model = self.registry('ir.model.data')
        self.structure_model = self.registry("hr.payroll.structure")
        self.deduction_model = self.registry("hr.deduction.category")
        self.benefit_model = self.registry("hr.employee.benefit.category")
        self.input_model = self.registry("hr.payslip.input")
        self.benefit_rate_model = self.registry("hr.employee.benefit.rate")
        self.benefit_rate_line_model = self.registry(
            "hr.employee.benefit.rate.line")

        self.context = self.user_model.context_get(self.cr, self.uid)
        cr, uid, context = self.cr, self.uid, self.context

        # Create an employee and all his deductions
        self.employee_model.write(cr, uid, [self.employee_id], {
            'deduction_ids': [
                (0, 0, {
                    'category_id': self.get_deduction_id(ded[0]),
                    'date_start': '2014-01-01',
                    'date_end': '2014-12-31',
                    'amount': ded[1],
                }) for ded in [
                    ('rrsp', 15),
                    ('fitf2', 16),
                    ('fitu1', 17),
                    ('fithd', 936),
                    ('fitf1', 988),
                    ('fitk1', 1040),
                    ('fit_k3_char', 1092),
                ]
            ]
        }, context=context)

        # Get the canadian payroll structure
        self.structure_id = self.structure_model.search(
            cr, uid, [('code', '=', 'CA')], context=context)[0]

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
        self.contract_model.write(cr, uid, [self.contract_id], {
            'struct_id': self.structure_id,
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
            ]
        }, context=context)

        self.payslip_vals = {
            'company_id': self.company_id,
            'employee_id': self.employee_id,
            'contract_id': self.contract_id,
            'date_from': '2014-01-01',
            'date_to': '2014-01-07',
            'date_payment': '2014-01-07',
            'struct_id': self.structure_id,
        }

    def create_worked_days(self, wd_lines):
        cr, uid, context = self.cr, self.uid, self.context

        for wd in wd_lines:
            self.worked_days_model.create(
                cr, uid, {
                    'payslip_id': self.payslip_1_id,
                    'date': wd[0],
                    'activity_id': wd[1],
                    'number_of_hours': wd[2],
                    'hourly_rate': wd[3],
                }, context=context)

    def create_inputs(self, input_lines):
        cr, uid, context = self.cr, self.uid, self.context

        for input_line in input_lines:
            self.input_model.create(
                cr, uid, {
                    'name': 'Test',
                    'payslip_id': self.payslip_1_id,
                    'category_id': input_line[0],
                    'amount': input_line[1],
                }, context=context)

    def compute_payslip(self):
        """ Compute the payslip and return a dict containing the
        payslip lines """
        cr, uid, context = self.cr, self.uid, self.context

        self.payslip_model.compute_sheet(
            cr, uid, [self.payslip_1_id], context=context)

        return self.get_payslip_lines(self.payslip_1_id)


class TestCanadaPayrollStructure(TestPayrollStructureBase):
    """ Test the Canada payroll structure """

    def test_create_payslip_low_wage(self):
        self.payslip_1_id = self.create_payslip(self.payslip_vals)
        self.create_worked_days([
            # (date,  activity_id, nb_hours, hourly_rate)
            ('2014-01-01', self.job_activity_id, 40, 20),
        ])
        self.create_inputs([
            (self.ref('payslip_input_bonus'), 30),
            (self.ref('payslip_input_retro_pay'), 70)
        ])

        payslip = self.compute_payslip()

        p = 52
        self.assertEqual(payslip['GROSSP'], 40 * 20)

        self.assertEqual(
            payslip['FIT_I'],
            round(payslip['GROSSP'] * (1 + 0.008 + 0.018), 2))

        self.assertEqual(
            payslip['FIT_I_OTHER_WAGE'],
            payslip['FIT_I'] + payslip['OTHER_WAGE'])

        pension_rate = 0.001 + 0.004 + 0.008 + 0.009 + 0.018

        self.assertEqual(
            payslip['FIT_F'],
            15 + pension_rate * payslip['GROSSP'])
        self.assertEqual(payslip['FIT_F2'], 16)
        self.assertEqual(payslip['FIT_U1'], 17)
        self.assertEqual(payslip['FIT_HD'], 936)
        self.assertEqual(payslip['FIT_F1'], 988)

        self.assertEqual(
            round(payslip['FIT_A']), round(payslip['FIT_I'] * p - (
                payslip['FIT_F'] + 16 + 17) * p - 936 - 988))

        # the k2 tax credit is based on ei and cpp contributions
        self.assertEqual(
            round(payslip['FIT_K2']),
            round((payslip['EI_EE_C'] + payslip['CPP_EE_C']) * p))

        self.assertEqual(
            round(payslip['FIT_T3']),
            round((
                payslip['FIT_A'] - ((20 + 21) * p + payslip['FIT_K2'] + 1127)
            ) * 0.15)
        )

        self.assertEqual(
            round(payslip['FIT_T']),
            round((payslip['FIT_T3'] / p + 100 * 0.15)))

    def test_create_payslip_higher_wage(self):
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
            payslip['FIT_I'],
            round(payslip['GROSSP'] * (1 + 0.008 + 0.018), 2))

        self.assertEqual(
            payslip['FIT_I_OTHER_WAGE'],
            payslip['FIT_I'] + payslip['OTHER_WAGE'])

        pension_rate = 0.001 + 0.004 + 0.008 + 0.009 + 0.018

        self.assertEqual(
            round(payslip['FIT_A']), round(payslip['FIT_I'] * p - (
                pension_rate * payslip['GROSSP'] + 15 + 16 + 17 + 18 + 19) * p)
        )

        # the k2 tax credit is based on ei and cpp contributions
        self.assertEqual(round(payslip['FIT_K2']), round(913.68 + 2425.50))

        self.assertEqual(
            round(payslip['FIT_T3']),
            round((
                payslip['FIT_A'] * 0.22 - 3077 -
                ((20 + 21) * p + payslip['FIT_K2'] + 1127) * 0.15)))

        self.assertEqual(
            round(payslip['FIT_T']),
            round((payslip['FIT_T3'] / p + 1000 * 0.22)))

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
                'company_id': self.company_id,
                'employee_id': self.employee_id,
                'contract_id': self.contract_id,
                'date_from': ps[1],
                'date_to': ps[2],
                'date_payment': ps[2],
                'struct_id': self.structure_id,
            }) for ps in [
                (1, '2014-01-01', '2014-03-31'),
                (2, '2014-04-01', '2014-06-30'),
                (3, '2014-07-01', '2014-09-30'),
                (4, '2014-10-01', '2014-12-31'),
            ]
        }

        self.contract_model.write(
            cr, uid, [self.contract_id], {
                'wage': 83200,
                'schedule_pay': 'quarterly',
                'worked_hours_per_pay_period': 520,
            }, context=context)

        # Create the worked_days records
        for wd in [
            # (date_from, date_to, activity_id, nb_hours, hourly_rate)
            ('2014-01-01', self.job_activity_id, 520, 40, 1),
            ('2014-04-01', self.job_activity_id, 520, 40, 2),
            ('2014-07-01', self.job_activity_id, 520, 40, 3),
            ('2014-10-01', self.job_activity_id, 520, 40, 4),
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

        for payslip in [payslips[1], payslips[2], payslips[3], payslips[4]]:
            self.payslip_model.compute_sheet(
                cr, uid, [payslip],
                context=context)
            self.payslip_model.write(
                cr, uid, [payslip], {
                    'state': 'done',
                }, context=context)

        payslip2 = self.get_payslip_lines(payslips[2])
        payslip4 = self.get_payslip_lines(payslips[4])

        self.assertEqual(payslip4['GROSSP'], 520 * 40)

        taxable_income = payslip4['GROSSP'] * (1 + 0.008 + 0.018)

        # Canada pension plan
        self.assertEqual(payslip4['CPP_EE_C'], 0)
        self.assertEqual(
            round(payslip2['CPP_EE_C']),
            round((taxable_income + 30 + 70 - 3500 / 4) * 0.0495))

        self.assertEqual(payslip4['CPP_ER_C'], 0)
        self.assertEqual(payslip2['CPP_ER_C'], payslip2['CPP_EE_C'])

        # Employment insurance
        self.assertEqual(round(payslip4['EI_EE_C']), 0)

        self.assertEqual(
            round(payslip2['EI_EE_C']),
            round((taxable_income + 30 + 70) * 0.0188))

        self.assertEqual(payslip4['EI_ER_C'], 0)
        self.assertEqual(
            round(payslip2['EI_ER_C']), round(payslip2['EI_EE_C'] * 1.4))

        # RRP
        self.assertEqual(
            payslip4['RPP_EE_C'], payslip4['GROSSP'] * 0.001)

        # the k2 tax credit is based on ei and cpp contributions
        self.assertEqual(payslip4['FIT_K2'], 913.68 + 2425.50)

        self.payslip_model.write(
            cr, uid, payslips.values(),
            {'state': 'draft'},
            context=context)

    def test_create_payslip_wage(self):
        """ Test the salary rules, when the employee is paid
        by wage instead of hourly rates and unpaid worked
        days were computed """
        cr, uid, context = self.cr, self.uid, self.context

        self.contract_model.write(cr, uid, [self.contract_id], {
            'salary_computation_method': 'yearly'
        }, context=context)

        self.payslip_1_id = self.create_payslip(self.payslip_vals)

        # Create the worked_days records including an unpaid day
        self.create_worked_days([
            # (date, activity_id, nb_hours, hourly_rate)
            ('2014-01-01', self.unpaid_activity_id, 8, 0),
            ('2014-01-02', self.job_activity_id, 7, 0),
        ])

        payslip = self.compute_payslip()

        self.assertEqual(payslip['GROSSP'], 52000 / 52 * (40 - 8) / 40)

        # Add 28 worked hours to the contract and recompute.
        # The paid worked hours now equal 35 (7 + 28)
        self.create_worked_days([
            # (date, activity_id, nb_hours, hourly_rate)
            ('2014-01-01', self.job_activity_id, 28, 0),
        ])

        self.payslip_model.compute_sheet(
            cr, uid, [self.payslip_1_id], context=context)

        payslip = self.get_payslip_lines(self.payslip_1_id)

        self.assertEqual(payslip['GROSSP'], 52000 / 52 * 35 / 40)

        # Add 10 worked hours to the contract and recompute.
        # The paid worked hours now equal 45 (7 + 28 + 10)
        # The employee is paid at full wage
        self.create_worked_days([
            # (date, activity_id, nb_hours, hourly_rate)
            ('2014-01-01', self.job_activity_id, 10, 0),
        ])

        self.payslip_model.compute_sheet(
            cr, uid, [self.payslip_1_id], context=context)

        payslip = self.get_payslip_lines(self.payslip_1_id)

        self.assertEqual(payslip['GROSSP'], 52000 / 52)
