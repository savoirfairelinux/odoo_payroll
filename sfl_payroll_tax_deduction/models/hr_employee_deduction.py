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


class HrEmployeeDeduction(models.Model):
    """Income Tax Deduction"""

    _name = 'hr.employee.deduction'
    _description = _(__doc__)

    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    category_id = fields.Many2one(
        'hr.deduction.category',
        'Deduction',
        required=True,
        ondelete='cascade',
    )
    amount = fields.Float(
        'Amount',
        required=True,
        help="It is used in computation of the payslip. "
        "May be an annual or periodic amount depending on the category. "
        "The deduction may be a tax credit.",
        default=0,
    )
    date_start = fields.Date(
        'Start Date',
        required=True,
    )
    date_end = fields.Date(
        'End Date'
    )
    amount_type = fields.Selection(
        [
            ('each_pay', 'Each Pay'),
            ('annual', 'Annual'),
        ],
        related='category_id.amount_type',
        type='char',
        readonly=True,
        string="Amount Type",
    )
    jurisdiction_id = fields.Many2one(
        'hr.deduction.jurisdiction',
        'Jurisdiction',
        related='category_id.jurisdiction_id',
        readonly=True,
    )

    @api.multi
    def onchange_category_id(self, category_id, amount):
        if not category_id:
            return {}

        category = self.env['hr.deduction.category'].browse(category_id)
        return {
            'amount': amount or category.default_amount,
            'amount_type': category.amount_type,
            'jurisdiction_id': category.jurisdiction_id.id,
        }
