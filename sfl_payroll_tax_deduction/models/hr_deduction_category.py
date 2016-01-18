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

from openerp import fields, models, _


class HrDeductionCategory(models.Model):
    """Income Tax Deduction Category"""

    _name = 'hr.deduction.category'
    _description = _(__doc__)

    name = fields.Char(
        'Category Name',
        required=True,
    )
    description = fields.Text(
        'Description',
        required=True,
        help="Brief explanation of which benefits the category contains.",
    )
    default_amount = fields.Float(
        'Default Amount',
        required=True,
        default=0,
    )
    amount_type = fields.Selection(
        [
            ('each_pay', 'Each Pay'),
            ('annual', 'Annual'),
        ],
        required=True,
        string="Amount Type",
        default='annual',
    )
    jurisdiction_id = fields.Many2one(
        'hr.deduction.jurisdiction',
        'Jurisdiction',
        required=True,
    )
    salary_rule_ids = fields.Many2many(
        'hr.salary.rule',
        string='Salary Rules',
        help='Salary Rules in which the deduction will be added',
    )
    active = fields.Boolean(
        'active',
        default=True,
    )
