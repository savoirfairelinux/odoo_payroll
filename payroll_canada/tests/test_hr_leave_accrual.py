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

from openerp.tests import common


class TestHrLeaveAccrual(common.TransactionCase):
    """
    Test the leave accruals of an employee in Canada
    """
    def ref(self, ext_id):
        if '.' in ext_id:
            module, ext_id = ext_id.split('.')
        else:
            module = 'payroll_canada'

        return self.data_model.get_object_reference(
            self.cr, self.uid, module, ext_id)[1]

    def setUp(self):
        super(TestHrLeaveAccrual, self).setUp()
        self.data_model = self.registry('ir.model.data')
        self.employee_model = self.registry('hr.employee')
        self.contract_model = self.registry("hr.contract")
        self.user_model = self.registry("res.users")
        self.accrual_model = self.registry("hr.leave.accrual")
        self.entitlement_model = self.registry("hr.holidays.entitlement")
        self.context = self.user_model.context_get(self.cr, self.uid)
        cr, uid, context = self.cr, self.uid, self.context

        self.employee_id = self.employee_model.create(
            cr, uid, {'name': 'Employee 1'}, context=context)

        # Searching the employee accrual creates the accrual if
        # if does not exist
        self.employee_model.get_leave_accrual(
            cr, uid, self.employee_id,
            leave_type_id=self.ref(
                'payroll_activity.holiday_status_vacation'),
            context=context)

        self.entitlement_id = self.entitlement_model.create(cr, uid, {
            'name': 'Custom Vacation Entitlement',
            'month_start': '5',
            'day_start': 15,
            'leave_id': self.ref(
                'payroll_activity.holiday_status_vacation'),
        })

        self.contract_id = self.contract_model.create(
            cr, uid, {
                'employee_id': self.employee_id,
                'name': 'Contract 1',
                'wage': 52000,
                'holidays_entitlement_ids': [(4, self.entitlement_id)],
            }, context=context)

        self.accrual_id = self.accrual_model.search(
            self.cr, self.uid, [('employee_id', '=', self.employee_id)],
            context=self.context)[0]

        self.accrual = self.accrual_model.browse(
            cr, uid, self.accrual_id, context=context)

        # Create lines to insert into leave accruals
        accrual_lines = [
            # Lines ignored
            ('2015-05-15', 200),
            ('2015-05-15', -700),

            ('2014-05-31', 30),
            ('2014-05-31', -75),

            ('2014-05-15', 70),
            ('2014-05-15', -110),

            ('2014-05-14', -15),
            ('2014-05-14', 270),
            ('2012-01-01', -35),
            ('2012-01-01', 290),
        ]

        line_ids = [
            (0, 0, {
                'source': 'manual',
                'date': accrual_line[0],
                'name': 'Test',
                'amount': accrual_line[1]
            }) for accrual_line in accrual_lines
        ]
        self.accrual.write({'line_cash_ids': line_ids})

    def test_sum_leaves_available(self):
        """
        Test that employee method sum_leaves_available returns a dict
        containing the right amount for current_added_ytd
        """
        res = self.accrual.sum_leaves_available('2014-05-31', in_cash=True)

        # Current year taken: -75 - 110 = -185
        # Previous ytd: -15 + 270 - 35 + 290 = 510
        self.assertEqual(res, 325)

    def test_sum_leaves_available_before_entitlement(self):
        """
        Test that employee method sum_leaves_available returns a dict
        containing the right amount for current_added_ytd
        """
        res = self.accrual.sum_leaves_available('2014-05-14', in_cash=True)

        # Current year taken: -15
        # Previous ytd: -35 + 290
        self.assertEqual(res, 290 - 35 - 15)

    def test_sum_leaves_available_at_entitlement(self):
        """
        Test that employee method sum_leaves_available returns a dict
        containing the right amount for current_added_ytd
        """
        res = self.accrual.sum_leaves_available('2014-05-15', in_cash=True)

        # Current year taken: -75 - 110 = -185
        # Previous ytd: -15 - 35 + 270 + 290 = 510
        self.assertEqual(res, 325)
