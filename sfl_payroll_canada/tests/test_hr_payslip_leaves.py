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

from openerp.osv import orm

from .test_payroll_structure import TestPayrollStructureBase


class TestHrPayslipLeaves(TestPayrollStructureBase):
    """
    Test methods that write or read worked days records or payslip inputs
    """
    def setUp(self):
        super(TestHrPayslipLeaves, self).setUp()

        self.context = self.user_model.context_get(self.cr, self.uid)
        cr, uid, context = self.cr, self.uid, self.context

        self.contract_model.write(cr, uid, [self.contract_id], {
            'schedule_pay': 'monthly',
            'worked_hours_per_pay_period': 160,
        }, context=context)

        self.payslip_id = self.create_payslip({
            'employee_id': self.employee_id,
            'contract_id': self.contract_id,
            'date_from': '2014-01-01',
            'date_to': '2014-01-31',
        })

        for line in [
            # date_from, date_to, nb_hours, activity_id, hourly_rate, rate (%)
            ('2014-01-01', '2014-01-01', 20, self.job_activity_id, 20, 100),
            ('2014-01-02', '2014-01-10', 20, self.job_activity_id, 20, 100),
            ('2014-01-31', '2014-01-31', 20, self.job_activity_id, 20, 100),

            ('2014-01-01', '2014-01-01', 20, self.sl_activity_id, 20, 100),
            ('2014-01-02', '2014-01-10', 20, self.comp_activity_id, 20, 100),
            ('2014-01-31', '2014-01-31', 20, self.public_activity_id, 20, 100),

            ('2014-01-01', '2014-01-01', 11, self.vac_activity_id, 15, 90),
            ('2014-01-02', '2014-01-10', 13, self.vac_activity_id, 10, 100),
            ('2014-01-31', '2014-01-31', 17, self.vac_activity_id, 25, 150),

        ]:
            self.worked_days_model.create(
                cr, uid, {
                    'date_from': line[0],
                    'date_to': line[1],
                    'number_of_hours': line[2],
                    'activity_id': line[3],
                    'hourly': line[4],
                    'rate': line[5],
                    'payslip_id': self.payslip_id,
                }, context=context)

        self.salary_rule = self.rule_model.browse(
            cr, uid, self.ref('rule_ca_vac_taken'), context=context)

    def test_check_max_leave_hours(self):
        cr, uid, context = self.cr, self.uid, self.context

        self.contract_model.write(
            cr, uid, [self.contract_id], {
                'salary_computation_method': 'yearly',
            }, context=context)

        # Already 101 leave hours
        # We add 60, so the total equals 161 > worked_hours_per_pay_period
        self.assertRaises(
            orm.except_orm,
            self.payslip_model.write,
            cr, uid, [self.payslip_id], {
                'worked_days_line_ids': [(0, 0, {
                    'date_from': '2014-01-01', 'date_to': '2014-01-01',
                    'number_of_hours': 60, 'activity_id': self.sl_activity_id,
                    'hourly': 20, 'rate': 100,
                })],
            }, context=context)

    def test_sum_leave_category_nb_hours(self):
        cr, uid, context = self.cr, self.uid, self.context

        payslip = self.payslip_model.browse(
            cr, uid, self.payslip_id, context=context)

        res = self.salary_rule.sum_leaves(payslip, in_cash=False)

        self.assertEqual(res, 11 + 13 + 17)

    def test_sum_leave_category_cash(self):
        cr, uid, context = self.cr, self.uid, self.context

        payslip = self.payslip_model.browse(
            cr, uid, self.payslip_id, context=context)

        res = self.salary_rule.sum_leaves(payslip, in_cash=True)

        self.assertEqual(
            res, 11 * 15 * 0.90
            + 13 * 10 * 1.0
            + 17 * 25 * 1.5
        )

    def test_reduce_leave_hours(self):
        """
        Test reduce_leave_hours with divide_by_rate=False
        """
        cr, uid, context = self.cr, self.uid, self.context

        payslip = self.payslip_model.browse(
            cr, uid, self.payslip_id, context=context)

        # Reduce the leave hours
        self.salary_rule.reduce_leaves(payslip, 20, in_cash=False)

        # Validate how many hours are left in the worked days
        res = self.salary_rule.sum_leaves(payslip, in_cash=False)

        self.assertEqual(res, 11 + 13 + 17 - 20)

    def test_reduce_leave_hours_cash(self):
        """
        Test reduce_leave_hours with divide_by_rate=True
        """
        cr, uid, context = self.cr, self.uid, self.context

        payslip = self.payslip_model.browse(
            cr, uid, self.payslip_id, context=context)

        # Reduce the leave hours
        self.salary_rule.reduce_leaves(payslip, 700, in_cash=True)

        # Validate how much cash is left in the worked days
        res = self.salary_rule.sum_leaves(payslip, in_cash=True)

        self.assertEqual(
            res, 11 * 15 * 0.90
            + 13 * 10 * 1.0
            + 17 * 25 * 1.5
            - 700
        )

        # Validate how many hours are left in the worked days
        res = self.salary_rule.sum_leaves(payslip, in_cash=False)

        # The method should reduce the worked days with the highest
        # date first
        reduction_jan_31 = 17 * 25 * 1.5
        reduction = 17 + (700 - reduction_jan_31) / (10 * 1.0)
        self.assertEqual(res, 11 + 13 + 17 - reduction)
