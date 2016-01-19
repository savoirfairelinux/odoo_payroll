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


class HrFiscalSlipBox(models.Model):
    """Fiscal Slip Box"""

    _name = 'hr.fiscal_slip.box'
    _description = _(__doc__)

    name = fields.Char(
        'Name', required=True, translate=True,
    )
    date_from = fields.Date(
        'Date From', required=True,
    )
    date_to = fields.Date(
        'Date To',
    )
    code = fields.Char(
        'Code',
    )
    xml_tag = fields.Char(
        'XML Tag',
    )
    is_other_amount = fields.Boolean(
        'Is Other Amount',
    )
    salary_rule_ids = fields.Many2many(
        'hr.salary.rule',
        'hr_fiscal_slip_box_salary_rule_rel',
        string='Salary Rules',
        readonly=True,
    )
    benefit_line_ids = fields.One2many(
        'hr.fiscal_slip.box.benefit.line',
        'box_id',
        'Benefit Categories',
    )
    deduction_line_ids = fields.One2many(
        'hr.fiscal_slip.box.deduction.line',
        'box_id',
        'Deduction Categories',
    )
    type = fields.Selection(
        [
            ('salary_rule', 'Salary Rules'),
            ('benefit', 'Benefit Categories'),
            ('deduction', 'Deduction Categories'),
        ],
        string='Type',
        required=True,
    )
    required = fields.Boolean(
        'Required',
        help="If box is required, it must have an amount "
        "even if it is null.",
    )

    appears_on_summary = fields.Boolean(
        'Appear On Summary XML',
    )

    _order = 'code'

    _defaults = {
        'required': False,
        'is_other_amount': False,
        'appears_on_summary': True,
    }

    @api.multi
    def compute_amount(self, payslip_ids):
        """
        Return the amount for a year for a given fiscal slip box

        :type payslip_ids: hr.payslip id list
        :rtype: float
        """
        self.ensure_one()

        if self.type == 'salary_rule':
            line_obj = self.env['hr.payslip.line']

            rule_ids = self.salary_rule_ids.ids

            lines = line_obj.search([
                ('slip_id', 'in', payslip_ids),
                ('salary_rule_id', 'in', rule_ids),
            ])
            return sum(
                -line.amount if line.slip_id.credit_note else line.amount
                for line in lines)

        total = 0

        if self.type == 'benefit':
            line_obj = self.env['hr.payslip.benefit.line']

            for benefit in self.benefit_line_ids:

                domain = [
                    ('payslip_id', 'in', payslip_ids),
                    ('payslip_id.date_payment', '>=', benefit.date_from),
                    ('category_id', '=', benefit.category_id.id),
                ]

                if benefit.date_to:
                    domain.append((
                        'payslip_id.date_payment', '<=', benefit.date_to))

                lines = line_obj.search(domain)

                if benefit.include_employee:
                    total += sum(
                        -line.employee_amount if line.payslip_id.credit_note
                        else line.employee_amount
                        for line in lines
                    )

                if benefit.include_employer:
                    total += sum(
                        -line.employer_amount if line.payslip_id.credit_note
                        else line.employer_amount
                        for line in lines
                    )

        else:
            line_obj = self.env['hr.payslip.deduction.line']

            for deduction in self.deduction_line_ids:

                domain = [
                    ('payslip_id', 'in', payslip_ids),
                    ('payslip_id.date_payment', '>=', deduction.date_from),
                    ('category_id', '=', deduction.category_id.id),
                ]

                if deduction.date_to:
                    domain.append((
                        'payslip_id.date_payment', '<=', deduction.date_to))

                lines = line_obj.search(domain)

                total += sum(
                    -line.amount if line.payslip_id.credit_note
                    else line.amount for line in lines)

        return total
