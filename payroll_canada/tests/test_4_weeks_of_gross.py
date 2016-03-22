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


class Test4WeeksOfGross(TestPayslipBase):
    """ Test the payslip method used to calculate the base amount for
    public holidays
    """

    def setUp(self):
        super(Test4WeeksOfGross, self).setUp()

        cr, uid, context = self.cr, self.uid, self.context

        self.company_model.write(cr, uid, [self.company_id], {
            'week_start': '1',
        }, context=context)

        self.employee_2_id = self.employee_model.create(cr, uid, {
            'name': 'Employee 1',
            'company_id': self.company_id,
        }, context=context)

        self.contract_2_id = self.contract_model.create(cr, uid, {
            'employee_id': self.employee_2_id,
            'name': 'Contract 2',
            'wage': 50000,
        }, context=context)

        self.payslip_ids = {
            line[0]: self.create_payslip({
                'employee_id': line[1],
                'contract_id': line[2],
                'date_from': line[3],
                'date_to': line[4],
                'date_payment': line[4],
            }) for line in [
                (1, self.employee_id, self.contract_id,
                    '2014-01-01', '2014-01-15'),
                (2, self.employee_id, self.contract_id,
                    '2014-01-16', '2014-01-31'),
                (3, self.employee_id, self.contract_id,
                    '2014-02-01', '2014-02-15'),
                (4, self.employee_id, self.contract_id,
                    '2014-02-16', '2014-02-28'),

                (5, self.employee_2_id, self.contract_2_id,
                    '2014-02-01', '2014-02-15'),
            ]
        }

        self.payslip_model.write(
            cr, uid,
            [self.payslip_ids[n] for n in [1, 2, 3, 5]],
            {'state': 'done'}, context=context)

        for line in [
            # Excluded
            ('2014-01-01', 5, 20, 100, self.payslip_ids[1]),
            ('2014-01-19', 7, 20, 100, self.payslip_ids[2]),

            # Included
            ('2014-01-20', 13, 20, 110, self.payslip_ids[2]),
            ('2014-02-04', 17, 25, 90, self.payslip_ids[3]),
            ('2014-02-16', 21, 35, 70, self.payslip_ids[4]),

            # Excluded
            ('2014-02-17', 31, 20, 100, self.payslip_ids[4]),

            # Excluded - Not the requested employee
            ('2014-02-10', 17, 20, 100, self.payslip_ids[5]),
        ]:
            self.worked_days_model.create(cr, uid, {
                'date': line[0],
                'number_of_hours': line[1],
                'activity_id': self.job_activity_id,
                'hourly_rate': line[2],
                'rate': line[3],
                'payslip_id': line[4],
            }, context=context)

    def compute_4_weeks_of_gross(self):
        cr, uid, context = self.cr, self.uid, self.context

        payslip = self.payslip_model.browse(
            cr, uid, self.payslip_ids[4], context=context)

        return payslip.get_4_weeks_of_gross(leave_date='2014-02-20')

    def test_get_4_weeks_of_gross(self):
        res = self.compute_4_weeks_of_gross()

        self.assertEqual(
            res,
            13 * 20 * 1.1 +
            17 * 25 * 0.9 +
            21 * 35 * 0.7
        )

    def test_get_4_weeks_of_gross_with_refunds(self):
        """ Tests the method get_4_weeks_of_gross with credit notes.
        """
        cr, uid, context = self.cr, self.uid, self.context

        # set payslips 2 and 3 as credit notes
        self.payslip_model.write(
            cr, uid, [self.payslip_ids[2], self.payslip_ids[3]],
            {'credit_note': True}, context=context)

        res = self.compute_4_weeks_of_gross()

        # Amounts in payslips no 2 and 3 are multiplied by -1
        self.assertEqual(
            res,
            (-13) * 20 * 1.1 +
            (-17) * 25 * 0.9 +
            21 * 35 * 0.7
        )
