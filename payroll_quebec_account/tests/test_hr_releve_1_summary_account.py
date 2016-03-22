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

from openerp.addons.payroll_quebec.tests.test_hr_releve_1_summary import (
    TestHrReleve1SummaryBase)


class TestHrReleve1SummaryAccount(TestHrReleve1SummaryBase):

    def setUp(self):

        super(TestHrReleve1SummaryAccount, self).setUp()
        self.setUp_qc_payroll_accounting()

        self.vals = {
            'hsf_salaries': 100000,
            'hsf_exemption_code': '06',
            'hsf_exemption_amount': 20000,
            'hsf_contribution_rate': 4.0,
            'hsf_reduction_basis': 25000,
            'hsf_reduction_rate': 2.0,
            'hsf_amount_remitted': 2000,

            'cnt_salaries': 200000,
            'cnt_rate': 0.08,

            'wsdrf_salaries': 700000,
            'wsdrf_rate': 1.0,
            'wsdrf_previous_reported': 1000,
            'wsdrf_expenses_current': 2250,
            'wsdrf_expenses': 3000,
        }

    def setUp_qc_payroll_accounting(self):
        cr, uid, context = self.cr, self.uid, self.context

        self.hsf_payable = self.create_account('payable', 2000001)
        self.hsf_expense = self.create_account('other', 5000001)

        hsf_rule_id = self.ref('payroll_quebec.rule_qc_hsf_er_c')

        self.rule_model.write(cr, uid, [hsf_rule_id], {
            'account_debit': self.hsf_expense.id,
            'account_credit': self.hsf_payable.id,
        }, context=context)

        self.cnt_payable = self.create_account('payable', 2000002)
        self.cnt_expense = self.create_account('other', 5000002)

        self.csst_payable = self.create_account('payable', 2000003)
        self.csst_expense = self.create_account('other', 5000003)

        self.wsdrf_payable = self.create_account('payable', 2000004)
        self.wsdrf_expense = self.create_account('other', 5000004)
        self.wsdrf_reported = self.create_account('other', 1000004)

        self.company_model.write(cr, uid, [self.company_id], {
            'payroll_journal_id': self.ref(
                'payroll_canada_account.payroll_journal'),

            'qc_cnt_debit_account': self.cnt_expense.id,
            'qc_cnt_credit_account': self.cnt_payable.id,

            'qc_wsdrf_debit_account': self.wsdrf_expense.id,
            'qc_wsdrf_credit_account': self.wsdrf_payable.id,
            'qc_wsdrf_reported_account': self.wsdrf_reported.id,
        }, context=context)

    def create_account(self, account_type, code):
        return self.env['account.account'].create({
            'name': 'Test',
            'code': code,
            'user_type_id': self.ref('account.data_account_type_payable')
            if account_type == 'payable'
            else self.ref('account.data_account_type_expenses'),
            'company_id': self.company_id,
            'reconcile': True if account_type == 'payable' else False,
        })

    def get_account_move_line(self, move, account):
        lines = [
            line for line in move.line_ids
            if line.account_id == account
        ]

        self.assertEqual(len(lines), 1)
        return lines[0]

    def prepare_summary(self):

        self.compute_payslips()

        summary = self.create_summary()
        summary.generate_slips()

        summary.write(self.vals)

        summary.button_confirm_slips()
        summary.button_confirm()
        summary.refresh()
        move = summary.move_id

        self.hsf_payable_line = self.get_account_move_line(
            move, self.hsf_payable)
        self.hsf_expense_line = self.get_account_move_line(
            move, self.hsf_expense)
        self.cnt_payable_line = self.get_account_move_line(
            move, self.cnt_payable)
        self.cnt_expense_line = self.get_account_move_line(
            move, self.cnt_expense)
        self.wsdrf_payable_line = self.get_account_move_line(
            move, self.wsdrf_payable)
        self.wsdrf_expense_line = self.get_account_move_line(
            move, self.wsdrf_expense)
        self.wsdrf_reported_line = self.get_account_move_line(
            move, self.wsdrf_reported)

    def test_releve_1_summary_account_entry(self):
        self.prepare_summary()

        # (100000 - 20000) * 4.0 % - 25000 * 2.0 % - 2000 = 700
        self.assertEqual(self.hsf_payable_line.credit, 700)
        self.assertEqual(self.hsf_expense_line.debit, 700)

        # 200000 * 0.08 % = 160
        self.assertEqual(self.cnt_payable_line.credit, 160)
        self.assertEqual(self.cnt_expense_line.debit, 160)

        # 700000 * 1.0 % - 3000 = 4000
        self.assertEqual(self.wsdrf_payable_line.credit, 4000)

        # 2250 - 3000
        self.assertEqual(self.wsdrf_reported_line.credit, 750)

        # 4000 + 750 = 4750
        self.assertEqual(self.wsdrf_expense_line.debit, 4750)

    def test_releve_1_summary_account_entry_2(self):
        self.vals['hsf_amount_remitted'] = 12000
        self.vals['wsdrf_expenses_current'] = 7500

        self.prepare_summary()

        # (100000 - 20000) * 4.0 % - 25000 * 2.0 % - 12000 = -9300
        self.assertEqual(self.hsf_payable_line.debit, 9300)
        self.assertEqual(self.hsf_expense_line.credit, 9300)

        # 700000 * 1.0 % - 3000 = 4000
        self.assertEqual(self.wsdrf_payable_line.credit, 4000)

        # 7500 - 3000 = 4500
        self.assertEqual(self.wsdrf_reported_line.debit, 4500)

        # 4000 - 4500 = -500
        self.assertEqual(self.wsdrf_expense_line.credit, 500)
