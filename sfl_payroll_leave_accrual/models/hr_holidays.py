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

from openerp import api, fields, models


class HrHolidays(models.Model):

    _inherit = 'hr.holidays'

    accrual_line_id = fields.One2many(
        'hr.leave.accrual.line',
        'allocation_id',
        'Leave Accrual Line',
    )

    @api.multi
    def holidays_validate(self):
        """
        After an allocation of holidays is validated,
        add hours to the related leave accrual of the employee
        """
        res = super(HrHolidays, self).holidays_validate()
        self.cancel_leave_accrual_lines()
        self.compute_leave_accrual_lines()
        return res

    @api.multi
    def cancel_leave_accrual_lines(self):
        self.mapped('accrual_line_id').unlink()

    @api.one
    def compute_leave_accrual_lines(self):
        if (
            self.type == 'add' and self.holiday_type == 'employee' and
            self.holiday_status_id.increase_accrual_on_allocation
        ):
            employee = self.employee_id
            leave_type = self.holiday_status_id

            accrual = self.employee.get_leave_accrual_id(
                leave_type_id=leave_type.id)

            number_of_hours = (
                self.number_of_days_temp *
                employee.company_id.holidays_hours_per_day)

            self.write({
                'accrual_line_id': [(0, 0, {
                    'name': self.name,
                    'source': 'allocation',
                    'amount': number_of_hours,
                    'accrual_id': accrual.id,
                    'date': fields.Date.today(),
                    'amount_type': 'hours',
                })]})

    def holidays_refuse(self, cr, uid, ids, context=None):
        """
        After an allocation of holidays is refused,
        remove the leave accrual line related
        """
        res = super(HrHolidays, self).holidays_refuse()
        self.cancel_leave_accrual_lines()
        return res
