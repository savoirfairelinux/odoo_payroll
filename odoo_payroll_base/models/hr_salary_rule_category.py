# -*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>)
#    Copyright (C) 2015 Savoir-faire Linux
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

from openerp import fields, models


class hr_salary_rule_category(models.Model):
    _name = 'hr.salary.rule.category'
    _description = 'Salary Rule Category'
    name = fields.Char(
        'Name',
        required=True,
    )
    code = fields.Char(
        'Code',
        required=True,
    )
    parent_id = fields.Many2one(
        'hr.salary.rule.category',
        'Parent',
        help="Linking a salary category to its parent is used "
        "only for the reporting purpose.",
    )
    children_ids = fields.One2many(
        'hr.salary.rule.category',
        'parent_id',
        'Children',
    )
    note = fields.Text(
        'Description',
    )
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.user.company_id.id,
    )
