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
        self.job_model = self.env["hr.job"]
        self.activity_model = self.env['hr.activity']
        self.worked_days_model = self.env['hr.payslip.worked_days']

        self.job = self.job_model.create({
            'name': 'Job 1',
        })

        self.job_2 = self.job_model.create({
            'name': 'Job 2',
        })

        self.activity_1 = self.job.activity_ids[0]

        self.activity_2 = self.job_2.activity_ids[0]

        self.activity_3 = self.activity_model.search(
            [('activity_type', '=', 'leave')])[0]

        self.contract.write({
            'contract_job_ids': [
                (0, 0, {
                    'job_id': self.job.id,
                    'is_main_job': True,
                }),
                (0, 0, {
                    'job_id': self.job_2.id,
                    'is_main_job': False,
                }),
            ],
        })

        self.rate_per_hour_1 = self.rate_model.create({
            'name': 'Test',
            'category_id': self.categories[0].id,
            'amount_type': 'per_hour',
        })

        self.rate_per_hour_2 = self.rate_model.create({
            'name': 'Test',
            'category_id': self.categories[1].id,
            'amount_type': 'per_hour',
        })

        for line in [
            (2, 4, '2015-01-01', '2015-01-15', self.rate_per_hour_1),
            (3, 5, '2015-01-16', False, self.rate_per_hour_1),

            (6, 8, '2015-01-01', '2015-01-15', self.rate_per_hour_2),
            (7, 9, '2015-01-16', False, self.rate_per_hour_2),
        ]:
            self.rate_line_model.create({
                'employee_amount': line[0],
                'employer_amount': line[1],
                'date_start': line[2],
                'date_end': line[3],
                'parent_id': line[4].id,
            })

        benefits = self.env['hr.employee.benefit']
        for b in self.benefits:
            benefits += b
        benefits.unlink()

        for line in [
            ('2015-01-01', 8, self.activity_1.id),
            ('2015-01-16', 12, self.activity_2.id),
            ('2015-01-21', 10, self.activity_3.id),
        ]:
            self.worked_days_model.create(
                {
                    'date': line[0],
                    'number_of_hours': line[1],
                    'activity_id': line[2],
                    'hourly_rate': 0,
                    'rate': 100,
                    'payslip_id': self.payslip.id,
                })

    def test_benefits_per_hour_on_jobs(self):

        for benefit in [
            (self.categories[0], self.rate_per_hour_1,
                '2015-01-01', '2015-12-31', self.job),
            (self.categories[1], self.rate_per_hour_2,
                '2015-01-01', '2015-12-31', self.job_2),
        ]:
            self.benefit_model.create({
                'category_id': benefit[0].id,
                'rate_id': benefit[1].id,
                'date_start': benefit[2],
                'date_end': benefit[3],
                'job_id': benefit[4].id,
            })

        payslip = self.compute_payslip()

        rule_1_total = (8 * 2) + (12 * 7)
        self.assertEqual(payslip['RULE_1'], rule_1_total)

        rule_2_total = (12 * 9)
        self.assertEqual(payslip['RULE_2'], rule_2_total)

    def test_benefits_per_hour_on_contract(self):

        for benefit in [
            (self.categories[0], self.rate_per_hour_1,
                '2015-01-01', '2015-12-31'),
            (self.categories[1], self.rate_per_hour_2,
                '2015-01-01', '2015-12-31'),
        ]:
            self.benefit_model.create({
                'category_id': benefit[0].id,
                'rate_id': benefit[1].id,
                'date_start': benefit[2],
                'date_end': benefit[3],
                'contract_id': self.contract.id,
            })

        payslip = self.compute_payslip()

        rule_1_total = (
            (8 * 2) + (12 * 3) +
            (8 * 6) + (12 * 7)
        )
        self.assertEqual(payslip['RULE_1'], rule_1_total)

        rule_2_total = (
            (8 * 8) + (12 * 9)
        )
        self.assertEqual(payslip['RULE_2'], rule_2_total)
