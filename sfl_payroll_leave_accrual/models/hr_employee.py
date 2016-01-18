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

from openerp import api, fields, models


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    leave_accrual_ids = fields.One2many(
        'hr.leave.accrual',
        'employee_id',
        'Leave Accruals',
    )

    @api.multi
    def get_leave_accrual(self, leave_type_id):
        """
        Get the leave accrual of an employee, given a leave type

        leave_type_id: holidays.status id

        :return: leave accrual record
        """
        self.ensure_one()

        leave_type = self.env['hr.holidays.status'].browse(leave_type_id)

        existing_accrual = self.leave_accrual_ids.filtered(
            lambda a: a.leave_type_id == leave_type)

        if existing_accrual:
            return existing_accrual[0]

        # If the employee doesn't have the accrual of the given type,
        # create it
        new_accrual = self.env['hr.leave.accrual'].create({
            'employee_id': self.id,
            'leave_type_id': leave_type_id,
        })

        return new_accrual
