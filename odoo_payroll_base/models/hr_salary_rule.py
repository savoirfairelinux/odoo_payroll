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

from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp


class hr_salary_rule(models.Model):

    _name = 'hr.salary.rule'
    name = fields.Char(
        'Name', required=True, readonly=False
    )
    code = fields.Char(
        'Code',
        size=64,
        required=True,
        help="The code of salary rules can be used as reference in "
        "computation of other rules. In that case, it is case sensitive."
    )
    sequence = fields.Integer(
        'Sequence',
        required=True,
        help='Use to arrange calculation sequence',
        select=True,
        default=5,
    )
    quantity = fields.Char(
        'Quantity',
        help="It is used in computation for percentage and fixed "
        "amount.For e.g. A rule for Meal Voucher having fixed "
        "amount of 1€ per worked day can have its quantity defined "
        "in expression like worked_days.WORK100.number_of_days.",
        default=1,
    )
    category_id = fields.Many2one(
        'hr.salary.rule.category',
        'Category',
        required=True
    )
    active = fields.Boolean(
        'Active',
        help="If the active field is set to false, it will allow "
        "you to hide the salary rule without removing it.",
        default=True,
    )
    appears_on_payslip = fields.Boolean(
        'Appears on Payslip',
        help="Used to display the salary rule on payslip.",
        default=True,
    )
    parent_rule_id = fields.Many2one(
        'hr.salary.rule', 'Parent Salary Rule', select=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=False,
        default=lambda self: self.env.user.company_id.id,
    )
    condition_select = fields.Selection(
        [
            ('none', 'Always True'),
            ('range', 'Range'),
            ('python', 'Python Expression')
        ],
        "Condition Based on",
        required=True,
        default='none',
    )
    condition_range = fields.Char(
        'Range Based on', readonly=False,
        help="This will be used to compute "
        "the % fields values; in general it is on basic, "
        "but you can also use categories code fields in lowercase "
        "as a variable names (hra, ma, lta, etc.) and the variable basic."
    )
    condition_python = fields.Text(
        'Python Condition',
        required=True,
        readonly=False,
        help="Applied this rule for calculation if condition is true. "
        "You can specify condition like basic > 1000.",
        default=' ',
    )
    condition_range_min = fields.Float(
        'Minimum Range',
        required=False,
        help="The minimum amount, applied for this rule.",
    )
    condition_range_max = fields.Float(
        'Maximum Range',
        required=False,
        help="The maximum amount, applied for this rule.",
    )
    amount_select = fields.Selection(
        [
            ('percentage', 'Percentage (%)'),
            ('fix', 'Fixed Amount'),
            ('code', 'Python Code'),
        ],
        'Amount Type',
        select=True,
        required=True,
        help="The computation method for the rule amount.",
        default='fix',
    )
    amount_fix = fields.Float(
        'Fixed Amount',
        digits_compute=dp.get_precision('Payroll'),
        default=0,
    )

    amount_percentage = fields.Float(
        'Percentage (%)',
        digits_compute=dp.get_precision('Payroll Rate'),
        help='For example, enter 50.0 to apply a percentage of 50%',
        default=0.0,
    )
    amount_python_compute = fields.Text(
        'Python Code',
        default=' ',
    )
    amount_percentage_base = fields.Char(
        'Percentage based on',
        required=False,
        readonly=False,
        help='result will be affected to a variable'
    )
    child_ids = fields.One2many(
        'hr.salary.rule',
        'parent_rule_id',
        'Child Salary Rule',
        copy=True,
    )
    input_ids = fields.One2many(
        'hr.rule.input',
        'input_id',
        'Inputs',
        copy=True,
    )
    note = fields.Text(
        'Description',
    )

    @api.multi
    def _recursive_search_of_rules(self):
        """
        :return: record set of hr.salary.rule containing the rule's children
        """
        return self.search([
            ('parent_rule_id', 'child_of', self.ids),
        ])

    @api.multi
    def compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to
        compute the rule
        :return: returns a tuple build as the base/amount computed, the
        quantity and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()

        if self.amount_select == 'fix':
            try:
                return (
                    self.amount_fix,
                    float(eval(self.quantity, localdict)),
                    100.0
                )
            except:
                raise ValidationError(
                    _('Wrong quantity defined for salary rule %s (%s).') % (
                        self.name, self.code
                    ))

        elif self.amount_select == 'percentage':
            try:
                return (
                    float(eval(self.amount_percentage_base, localdict)),
                    float(eval(self.quantity, localdict)),
                    self.amount_percentage
                )
            except:
                raise ValidationError(
                    _('Wrong percentage base or quantity defined for '
                      'salary rule %s (%s).') % (self.name, self.code))

        else:
            try:
                eval(
                    self.amount_python_compute,
                    localdict, mode='exec', nocopy=True
                )
                return (
                    float(localdict['result']),
                    'result_qty' in localdict and
                    localdict['result_qty'] or 1.0,
                    'result_rate' in localdict and
                    localdict['result_rate'] or 100.0
                )
            except:
                raise ValidationError(
                    _('Wrong python code defined for salary rule %s (%s).') %
                    (self.name, self.code))

    @api.multi
    def satisfy_condition(self, localdict):
        """
        :return: True if the given rule match the condition.
        False otherwise.
        """
        self.ensure_one()

        if self.condition_select == 'none':
            return True

        elif self.condition_select == 'range':
            try:
                result = eval(self.condition_range, localdict)
                return (
                    self.condition_range_min <= result and
                    result <= self.condition_range_max or False
                )
            except:
                raise ValidationError(
                    _('Wrong range condition defined for salary '
                      'rule %s (%s).') %
                    (self.name, self.code))
        else:
            try:
                eval(
                    self.condition_python,
                    localdict, mode='exec', nocopy=True
                )
                return 'result' in localdict and localdict['result'] or False
            except:
                raise ValidationError(
                    _('Wrong python condition defined for salary '
                      'rule %s (%s).') %
                    (self.name, self.code))
