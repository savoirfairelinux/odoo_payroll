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
from openerp.exceptions import ValidationError


class HrSalaryRule(models.Model):

    _inherit = 'hr.salary.rule'

    accrual_line_ids = fields.One2many(
        'hr.holidays.status.accrual.line',
        'salary_rule_id',
        'Accrual Lines',
    )
    leave_type_id = fields.Many2one(
        'hr.holidays.status',
        'Leave Accrual',
    )

    @api.multi
    def get_leave_accrual(self):
        """
        If a salary rule is used to read or update a leave accrual,
        a leave type must be related to it.
        """
        self.ensure_one()

        if not self.leave_type_id:
            raise ValidationError(
                _('Error'),
                _('Salary rule %s is used to read leave '
                    'accruals but it has no related leave accrual.') % (
                    self.name))

        return self.leave_type_id

    @api.multi
    def sum_leave_accruals(self, payslip, in_cash=False):
        """
        Sum over the lines of an employee's leave accruals available for
        the current payslip
        """
        self.ensure_one()

        accrual = payslip.employee_id.get_leave_accrual(
            leave_type_id=self.leave_type_id.id)

        return accrual.sum_leaves_available(payslip.date_to, in_cash=in_cash)

    @api.multi
    def allow_override_limit(self):
        """
        Return True if the leave type related to the salary rule allows
        to override the limit allowed to the employee.

        This is used to know whether the employee is allowed to
        be paid amounts for a leave type for which he has not already accruded
        enough cash.
        """
        self.ensure_one()
        return self.leave_type_id.limit

    @api.multi
    def sum_payslip_input(self, payslip):
        """
        Sum over the other input lines of the payslip for a given
        input type
        :param payslip: BrowsablePayslip object or browse_record
        """
        self.ensure_one()

        categories = self.payslip_input_ids

        return sum(
            l.amount for l in payslip.input_line_ids
            if l.category_id in categories
        )

    @api.multi
    def reduce_payslip_input_amount(self, payslip, reduction):
        """
        When unused leaves requested are lower then those available,
        reduce the related inputs
        """
        self.ensure_one()

        assert reduction >= 0

        categories = self.payslip_input_ids
        categories.ensure_one()

        input_lines = payslip.input_line_ids.filtered(
            lambda l: l.category_id in categories)

        for input_line in input_lines:
            if reduction == 0:
                break

            current_reduction = min(input_line.amount, reduction)
            new_amount = input_line.amount - current_reduction

            input_line.write({'amount': new_amount})
            reduction = reduction - current_reduction
