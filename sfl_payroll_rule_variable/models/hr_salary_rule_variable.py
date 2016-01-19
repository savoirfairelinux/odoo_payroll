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

from openerp import models, fields, _


class HrSalaryRuleVariable(models.Model):
    """Salary Rule Variable"""

    _name = 'hr.salary.rule.variable'
    _description = _(__doc__)

    salary_rule_id = fields.Many2one(
        'hr.salary.rule',
        'Salary Rule',
        ondelete='cascade',
        required=True,
        index=True,
    )
    date_from = fields.Date(
        'Date From',
        required=True,
    )
    date_to = fields.Date(
        'Date To',
    )
    variable_type = fields.Selection(
        [
            ('python', 'Python Code'),
            ('fixed', 'Fixed Amount')
        ],
        type='char',
        string='Type',
        default="python",
    )
    python_code = fields.Text(
        'Python Code',
    )
    fixed_amount = fields.Float(
        'Fixed Amount',
    )
