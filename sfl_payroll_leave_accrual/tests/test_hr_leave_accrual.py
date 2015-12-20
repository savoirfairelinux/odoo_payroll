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

from openerp.tests import common


class TestHrLeaveAccrual(common.TransactionCase):

    def setUp(self):
        super(TestHrLeaveAccrual, self).setUp()

        self.employee = self.env['hr.employee'].create({
            'name': 'Employee 1'
        })

        self.leave_type = self.env['hr.holidays.status'].create({
            'name': 'Leave Test',
        })

        self.accrual = self.employee.get_leave_accrual(self.leave_type.id)

    def test_accrual_amount_precision(self):
        self.env['hr.leave.accrual.line'].create({
            'accrual_id': self.accrual.id,
            'amount_hours': 1.2345,
            'name': 'Test',
        })

        self.env['hr.leave.accrual.line'].create({
            'accrual_id': self.accrual.id,
            'amount_cash': 1.25,
            'name': 'Test',
        })

        self.assertEquals(self.accrual.total_hours, 1.2345)
        self.assertEquals(self.accrual.total_cash, 1.25)

    def test_accrual_is_refund(self):

        self.contract = self.env['hr.contract'].create({
            'employee_id': self.employee.id,
            'name': 'Contract 1',
            'wage': 50000,
        })

        self.payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'date_from': '2015-01-01',
            'date_to': '2015-01-31',
            'credit_note': True,
        })

        self.env['hr.leave.accrual.line'].create({
            'accrual_id': self.accrual.id,
            'amount_hours': 7,
            'name': 'Test',
        })

        self.env['hr.leave.accrual.line'].create({
            'accrual_id': self.accrual.id,
            'amount_hours': 3,
            'name': 'Test',
            'payslip_id': self.payslip.id,
        })

        self.env['hr.leave.accrual.line'].create({
            'accrual_id': self.accrual.id,
            'amount_cash': 5,
            'name': 'Test',
        })

        self.env['hr.leave.accrual.line'].create({
            'accrual_id': self.accrual.id,
            'amount_cash': 2,
            'name': 'Test',
            'payslip_id': self.payslip.id,
        })

        self.assertEquals(self.accrual.total_hours, 4)
        self.assertEquals(self.accrual.total_cash, 3)
