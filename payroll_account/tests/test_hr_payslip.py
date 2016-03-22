# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015 Savoir-faire Linux
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

from datetime import datetime

from dateutil.relativedelta import relativedelta

from openerp.addons.payroll_base.tests.test_hr_contract import (
    TestHrContractBase
)


class TestHrPayslip(TestHrContractBase):
    def setUp(self):
        super(TestHrPayslip, self).setUp()

        account_model = self.env['account.account']

        acc_payable = account_model.create({
            'name': 'Account Payable',
            'code': '100001',
            'user_type_id': self.ref('account.data_account_type_payable'),
            'reconcile': True,
        })

        acc_liquidity = account_model.create({
            'name': 'Account Liquidity',
            'code': '100002',
            'user_type_id': self.ref('account.data_account_type_liquidity'),
        })

        acc_expense = account_model.create({
            'name': 'Account Expense',
            'code': '100003',
            'user_type_id': self.ref('account.data_account_type_expenses'),
        })

        analytic_acc = self.env['account.analytic.account'].create({
            'name': 'Payroll Analytic Account',
            'code': '100000',
        })

        self.rule_1.write({
            'analytic_account_id': analytic_acc.id,
            'account_debit': acc_payable.id,
            'account_credit': acc_expense.id,
        })

        self.rule_4_1.write({
            'account_debit': acc_liquidity.id,
            'account_credit': acc_payable.id,
        })

        self.date_from = datetime.now() - relativedelta(weeks=2)
        self.date_to = datetime.now() - relativedelta(weeks=1)
        self.journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
        ], limit=1)

        self.payslip_1 = self.env['hr.payslip'].create({
            'employee_id': self.employee_1.id,
            'contract_id': self.contract_1.id,
            'struct_id': self.structure_4.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'date_payment': datetime.now(),
            'journal_id': self.journal.id,
        })

    def test_payslip_account_move(self):
        self.payslip_1.compute_sheet()
        self.payslip_1.process_sheet()

        move = self.payslip_1.move_id

        self.assertEqual(move.date, self.payslip_1.date_payment)

        self.assertEqual(len(move.line_ids), 4)
