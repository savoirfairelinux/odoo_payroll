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


class HrHolidaysStatusAccrualLine(models.Model):
    """Leave Type Accrual Line"""

    _name = 'hr.holidays.status.accrual.line'
    _description = _(__doc__)

    leave_type_id = fields.Many2one(
        'hr.holidays.status',
        'Leave Type',
        required=True,
    )
    salary_rule_id = fields.Many2one(
        'hr.salary.rule',
        'Leave Accrual Rule',
    )
    substract = fields.Boolean(
        'Substract Amount',
        default=False,
    )
    amount_type = fields.Selection(
        [
            ('cash', 'Monetary'),
            ('hours', 'Hours'),
        ],
        string="Amount Type",
        default='cash',
    )
