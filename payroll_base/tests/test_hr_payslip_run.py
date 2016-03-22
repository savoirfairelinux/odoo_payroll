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

from .test_hr_contract import TestHrContractBase


class TestHrPayslipRunBase(TestHrContractBase):
    def setUp(self):
        super(TestHrPayslipRunBase, self).setUp()

        self.run_model = self.env['hr.payslip.run']
        self.wizard_model = self.env['hr.payslip.employees']

        self.date_from = datetime.now()
        self.date_to = self.date_from + relativedelta(weeks=1, days=-1)
        self.date_payment = self.date_from + relativedelta(weeks=2, days=-1)

        self.run_1 = self.run_model.create({
            'name': 'Test',
            'date_start': self.date_from,
            'date_end': self.date_to,
            'date_payment': self.date_payment,
        })


class TestHrPayslipRun(TestHrPayslipRunBase):
    def test_payslip_run_wizard(self):
        self.wizard_model = self.wizard_model.with_context(
            {'active_id': self.run_1.id})
        wizard = self.wizard_model.create({
            'employee_ids': [(4, self.employee_1.id)],
        })
        wizard.compute_sheet()

        self.assertEqual(len(self.run_1.slip_ids), 1)

        slip = self.run_1.slip_ids[0]
        self.assertEqual(slip.date_from, self.run_1.date_start)
        self.assertEqual(slip.date_from, self.run_1.date_start)
