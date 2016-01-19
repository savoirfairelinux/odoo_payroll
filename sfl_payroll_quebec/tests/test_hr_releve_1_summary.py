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

from .test_hr_releve_1 import TestHrReleve1Base


class TestHrReleve1SummaryBase(TestHrReleve1Base):

    def create_summary(self):
        cr, uid, context = self.cr, self.uid, self.context

        summary_id = self.summary_model.create(cr, uid, {
            'company_id': self.company_id,
            'year': 2014,
        }, context=context)

        return self.summary_model.browse(
            cr, uid, summary_id, context=context)


class TestHrReleve1Summary(TestHrReleve1SummaryBase):
    def test_compute_releve_1_summary(self):
        """
        Test that the releve 1 summary is computed properly
        """
        cr, uid, context = self.cr, self.uid, self.context

        self.compute_payslips()

        summary = self.create_summary()
        summary.generate_slips()

        self.assertEqual(len(summary.releve_1_ids), 2)

        employee = self.employee_model.browse(
            cr, uid, self.employee_id, context=context)

        for releve_1 in summary.releve_1_ids:
            self.assertTrue(releve_1.computed)

        releve_1 = next(
            rl_1 for rl_1 in summary.releve_1_ids
            if rl_1.employee_id == employee)

        second_releve_1 = next(
            rl_1 for rl_1 in summary.releve_1_ids
            if rl_1.employee_id != employee)

        self.releve_1_id = releve_1.id
        self.check_releve_1_values()

        # Generate slips a second time and verify that the
        # releve 1 reviously created won't be generated a second time
        summary.generate_slips()
        releve_1.refresh()

        self.assertEqual(len(summary.releve_1_ids), 2)
        self.assertIn(releve_1, summary.releve_1_ids)

        self.assertEqual(
            round(summary.qpp_amount_ee, 2),
            round(
                releve_1.get_amount('B') +
                second_releve_1.get_amount('B'), 2))
        self.assertEqual(
            round(summary.qpip_amount_ee, 2),
            round(
                releve_1.get_amount('H') +
                second_releve_1.get_amount('H'), 2))
        self.assertEqual(
            round(summary.qit_amount_1, 2),
            round(
                releve_1.get_amount('E') +
                second_releve_1.get_amount('E'), 2))

        payslip_1 = self.get_payslip_lines(self.payslip_ids[1])
        payslip_2 = self.get_payslip_lines(self.payslip_ids[2])

        self.assertEqual(
            round(summary.qpp_amount_er, 2),
            round(
                payslip_1['QPP_ER_C'] * 2 +
                payslip_2['QPP_ER_C'], 2))
        self.assertEqual(
            round(summary.qpip_amount_er, 2),
            round(
                payslip_1['PPIP_ER_C'] * 2 +
                payslip_2['PPIP_ER_C'], 2))

        self.assertEqual(
            round(summary.hsf_salaries, 2),
            round(
                payslip_1['HSF_EE_S'] * 2 +
                payslip_2['HSF_EE_S'], 2))

        self.assertEqual(
            round(summary.hsf_amount_remitted, 2),
            round(summary.hsf_salaries * 0.02, 2))

    def test_releve_1_summary_totals(self):
        """
        Test that the totals are computed correctly in the releve 1 summary
        """
        summary = self.create_summary()

        summary.write({
            'qpp_amount_ee': 100,
            'qpp_amount_er': 200,
            'qpip_amount_ee': 300,
            'qpip_amount_er': 400,
            'qit_amount_1': 500,
            'qit_amount_2': 600,
            'sub_total_remitted': 800,
        })

        self.assertEqual(summary.qpp_amount_total, 300)
        self.assertEqual(summary.qpip_amount_total, 700)
        self.assertEqual(summary.qit_amount_total, 1100)
        # 300 + 700 + 1100
        self.assertEqual(summary.sub_total_contribution, 2100)
        # 2100 - 800
        self.assertEqual(summary.sub_total_payable, 1300)

        summary.write({
            'hsf_salaries': 100000,
            'hsf_exemption_code': '06',
            'hsf_exemption_amount': 20000,
            'hsf_contribution_rate': 4.0,
        })

        # 80000 * 0.04
        self.assertEqual(summary.hsf_amount_before_reduction, 3200)

        summary.write({
            'hsf_reduction_basis': 25000,
            'hsf_reduction_rate': 2.0,
            'hsf_amount_remitted': 2000,
        })

        # 25000 * 0.02
        self.assertEqual(summary.hsf_reduction_amount, 500)

        # 3200 - 500 - 2000
        self.assertEqual(summary.hsf_amount_payable, 700)

        summary.write({
            'cnt_salaries': 200000,
            'cnt_rate': 0.08,
        })

        # 20000 * 0.08
        self.assertEqual(summary.cnt_amount_payable, 160)

        summary.write({
            'wsdrf_salaries': 700000,
            'wsdrf_rate': 1.0,
            'wsdrf_previous_reported': 1500,
            'wsdrf_expenses_current': 2000,
            'wsdrf_expenses': 3000,
        })

        self.assertEqual(summary.wsdrf_amount_before_expenses, 7000)
        self.assertEqual(summary.wsdrf_expenses_available, 3500)
        self.assertEqual(summary.wsdrf_reported, 500)
        self.assertEqual(summary.wsdrf_contribution, 4000)

        # 1300 + 700 + 160 + 4000
        self.assertEqual(summary.total_balance, 6160)
        self.assertEqual(summary.total_receivable, 0)
        self.assertEqual(summary.total_payable, 6160)

        summary.write({'hsf_amount_remitted': 12000})

        summary.refresh()
        self.assertEqual(summary.total_balance, -3840)
        self.assertEqual(summary.total_receivable, 3840)
        self.assertEqual(summary.total_payable, 0)
