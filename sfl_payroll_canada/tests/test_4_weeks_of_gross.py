# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by
#    the Free Software Foundation, either version 3 of the License, or
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
            {'state': 'done'},
        )

        for line in [
            # date_from, date_to, nb_hours, hourly_rate, rate (%), payslip_id,
            # contract_id

            # 100% excluded from the date_from - date_to interval
            ('2014-01-01', '2014-01-15', 5, 20, 100, self.payslip_ids[1],
                self.contract_id),
            ('2014-01-19', '2014-01-19', 7, 20, 100, self.payslip_ids[2],
                self.contract_id),

            # 60% included
            ('2014-01-18', '2014-01-22', 11, 20, 100, self.payslip_ids[2],
                self.contract_id),

            # 100% included
            ('2014-01-20', '2014-01-21', 13, 20, 110, self.payslip_ids[2],
                self.contract_id),
            ('2014-02-04', '2014-02-10', 17, 25, 90, self.payslip_ids[3],
                self.contract_id),
            ('2014-02-16', '2014-02-16', 21, 35, 70, self.payslip_ids[4],
                self.contract_id),

            # 50% included
            ('2014-02-16', '2014-02-17', 29, 20, 100, self.payslip_ids[4],
                self.contract_id),

            # 100% excluded
            ('2014-02-17', '2014-02-28', 31, 20, 100, self.payslip_ids[4],
                self.contract_id),

            # 100% excluded - Not the requested employee
            ('2014-02-04', '2014-02-10', 17, 20, 100, self.payslip_ids[5],
                self.contract_2_id),
        ]:
            self.worked_days_model.create(cr, uid, {
                'date_from': line[0],
                'date_to': line[1],
                'number_of_hours': line[2],
                'activity_id': self.job_activity_id,
                'hourly': line[3],
                'rate': line[4],
                'payslip_id': line[5],
                'code': 'ddd',
                'name': 'ddd',
                'contract_id': line[6],
            }, context=context)

    def compute_4_weeks_of_gross(self):
        cr, uid, context = self.cr, self.uid, self.context

        payslip = self.payslip_model.browse(
            cr, uid, self.payslip_ids[4], context=context)

        return payslip.get_4_weeks_of_gross(leave_date='2014-02-20')

    def test_get_4_weeks_of_gross(self):
        res = self.compute_4_weeks_of_gross()

        self.assertTrue(
            res ==
            11 * 20 * 1.0 * 0.60 +
            13 * 20 * 1.1 +
            17 * 25 * 0.9 +
            21 * 35 * 0.7 +
            29 * 20 * 1.0 * 0.50
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
        self.assertTrue(
            res ==
            11 * 20 * 1.0 * 0.60 * -1 +
            13 * 20 * 1.1 * -1 +
            17 * 25 * 0.9 * -1 +
            21 * 35 * 0.7 +
            29 * 20 * 1.0 * 0.50
        )
