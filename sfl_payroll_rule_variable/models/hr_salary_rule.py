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
from openerp.tools.safe_eval import safe_eval as eval


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    variable_ids = fields.One2many(
        'hr.salary.rule.variable',
        'salary_rule_id',
        'Variables',
    )

    @api.multi
    def variable(self, date, localdict=False):
        """
        Get a salary rule variable related to a salary rule for
        a period of time

        This method is called from the salary rule:
        rule.variable(payslip.date_from)

        By using the optional argument localdict, you can pass the value of
        salary rule already computed. Example:
        rule.variable(payslip.date_from, {'GROSS': GROSS})

        :rtype: fixed amount (a float) or a python object (most likely a dict)
        """
        self.ensure_one()

        # Find the salary rule variable related to that rule for the
        # requested period
        variable = self.variable_ids.filtered(
            lambda v: v.date_from <= date <= v.date_to)

        if not variable:
            raise ValidationError(
                _("The salary rule variable related to %s does not "
                    "exist for the date %s") %
                (self.code, date))

        if len(variable) > 1:
            raise ValidationError(
                _("%s salary rule variables related to %s exist for "
                    "the date %s") %
                (len(variable), self.code, date))

        if variable.variable_type == 'python':
            return eval(variable.python_code, localdict or {})
        else:
            return variable.fixed_amount
