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


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    leave_accrual_line_ids = fields.One2many(
        'hr.leave.accrual.line',
        'payslip_id',
        'Leave Accrual Lines',
    )

    @api.multi
    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()

        self = self.with_context({'disable_leave_accrual_update': True})
        self.compute_leave_accrual_lines()
        self = self.with_context({'disable_leave_accrual_update': False})

        return res

    @api.multi
    def process_sheet(self):
        res = super(HrPayslip, self).process_sheet()

        self.mapped('employee_id.leave_accrual_ids').update_totals()

        return res

    @api.multi
    def cancel_sheet(self):
        res = super(HrPayslip, self).cancel_sheet()

        self.mapped('employee_id.leave_accrual_ids').update_totals()

        return res

    @api.one
    def compute_leave_accrual_lines(self):
        """
        Update an employee's leave accruals with the amounts computed in the
        payslip.
        """
        salary_rules = self.details_by_salary_rule_category.mapped(
            'salary_rule_id')

        leave_accrual_lines = salary_rules.mapped('accrual_line_ids')

        required_rules = leave_accrual_lines.mapped('salary_rule_id')

        leave_types_required = leave_accrual_lines.mapped('leave_type_id')

        employee = self.employee_id
        accruals = self.env['hr.leave.accrual']

        for leave_type in leave_types_required:
            # If the leave accrual does not exist, it will be created
            accruals += employee.get_leave_accrual(leave_type.id)

        # Create a dict to access the required payslip lines by rule id.
        # This is a matter of performance because we iterate
        # only one time over each payslip line

        payslip_line_dict = {
            line.salary_rule_id.id: line
            for line in self.details_by_salary_rule_category
            if line.salary_rule_id in required_rules
        }

        accrual_line_obj = self.env['hr.leave.accrual.line']
        for accrual in accruals:
            for line in accrual.leave_type_id.accrual_line_ids:
                salary_rule_id = line.salary_rule_id.id

                if salary_rule_id in payslip_line_dict:
                    payslip_line = payslip_line_dict[salary_rule_id]

                    amount = (
                        payslip_line.amount if line.amount_type == 'cash'
                        else payslip_line.amount_precise
                    )

                    if line.substract:
                        amount *= -1

                    if payslip_line.amount:
                        vals = {
                            'accrual_id': accrual.id,
                            'name': payslip_line.name,
                            'source': 'payslip',
                            'payslip_id': self.id,
                            'payslip_line_id': payslip_line.id,
                            'amount': amount,
                            'accrual_id': accrual.id,
                            'amount_type': line.amount_type,
                            'date': self.date_from,
                        }
                        accrual_line_obj.create(vals)
