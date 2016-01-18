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

from openerp import api, fields, models, _


class HrHolidays(models.Model):

    _inherit = 'hr.holidays'

    accrual_line_ids = fields.One2many(
        'hr.leave.accrual.line.hours',
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

        self = self.with_context({'disable_leave_accrual_update': True})
        self.sudo().cancel_leave_accrual_lines()
        self.sudo().compute_leave_accrual_lines()
        self = self.with_context({'disable_leave_accrual_update': False})

        self.sudo().mapped('accrual_line_ids.accrual_id').update_totals()

        return res

    @api.multi
    def cancel_leave_accrual_lines(self):
        self.mapped('accrual_line_ids').unlink()

    @api.one
    def compute_leave_accrual_lines(self):
        if (
            self.type == 'add' and self.holiday_type == 'employee' and
            self.holiday_status_id.increase_accrual_on_allocation
        ):
            employee = self.employee_id
            leave_type = self.holiday_status_id

            accrual = self.employee_id.get_leave_accrual(leave_type.id)

            number_of_hours = (
                self.number_of_days_temp *
                employee.company_id.holidays_hours_per_day)

            self.write({
                'accrual_line_ids': [(0, 0, {
                    'name': self.name or _('Leave Allocation'),
                    'source': 'allocation',
                    'amount': number_of_hours,
                    'accrual_id': accrual.id,
                    'date': fields.Date.today(),
                })]})

    def holidays_refuse(self, cr, uid, ids, context=None):
        """
        After an allocation of holidays is refused,
        remove the leave accrual line related
        """
        res = super(HrHolidays, self).holidays_refuse()
        self.cancel_leave_accrual_lines()
        return res
