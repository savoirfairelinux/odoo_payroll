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

from itertools import chain

from openerp import fields, models, api, _
from openerp.osv import osv


class HrPayrollPeriod(models.Model):

    _name = 'hr.payroll.structure'
    _description = 'Salary Structure'

    name = fields.Char(
        'Name',
        required=True,
    )
    code = fields.Char(
        'Reference',
        size=64,
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        copy=False,
        default=lambda self: self.env.user.company_id.id,
    )
    note = fields.Text(
        'Description',
    )
    parent_id = fields.Many2one(
        'hr.payroll.structure',
        'Parent',
        default=lambda self:
        self.env.ref('odoo_payroll_base.structure_base').id,
    )
    children_ids = fields.One2many(
        'hr.payroll.structure',
        'parent_id',
        'Children',
        copy=True,
    )
    rule_ids = fields.Many2many(
        'hr.salary.rule',
        'hr_structure_salary_rule_rel',
        'struct_id',
        'rule_id',
        'Salary Rules',
    )

    _constraints = [
        (
            osv.osv._check_recursion,
            'Error ! You cannot create a recursive Salary Structure.',
            ['parent_id']
        ),
    ]

    @api.model
    def copy(self, res_id, default=None):
        code = _("%s (copy)") % self.browse(res_id).code
        default = dict(default or {}, code=code)
        return super(HrPayrollPeriod, self).copy(res_id, default)

    @api.multi
    def get_all_rules(self):
        """
        :return: record set of hr.salary.rule
        """
        parent_rules = list(chain(*self.mapped('rule_ids')))
        return self.env['hr.salary.rule'].search([
            ('parent_rule_id', 'child_of', parent_rules.ids)
        ])

    @api.multi
    def get_parent_structures(self):
        """
        :return: record set of hr.payroll.structure
        """
        res = self

        for struct in self:
            child = struct
            parent = child.parent_id

            while parent:
                res.add(parent)
                child = parent
                parent = child.parent_id

        return res
