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


def get_states(self):
    return [
        ('cancelled', _('Cancelled')),
        ('draft', _('Draft')),
        ('confirmed', _('Confirmed')),
        ('sent', _('Sent')),
    ]


class HrFiscalSlip(models.AbstractModel):
    """Fiscal Slip"""

    _name = 'hr.fiscal_slip'
    _description = _(__doc__)

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user.company_id.id,
    )
    address_home_id = fields.Many2one(
        'res.partner',
        'Home Address',
        related='employee_id.address_home_id',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    reference = fields.Char(
        'Reference',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    year = fields.Char(
        'Fiscal Year',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: int(fields.Date.today()[0:4]) - 1,
    )
    state = fields.Selection(
        get_states,
        'Status',
        type='char',
        select=True,
        required=True,
        default='draft',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    computed = fields.Boolean(
        'Computed',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    @api.model
    def get_rpp_dpsp_rgst_nbr(self, payslip_ids):
        """
        Find the RPP/DPSP registration number with the highest amount
        contributed in a list of payslips

        If the employee contributed, return the number with highest
        employee contribution, otherwise the highest employer contribution
        """
        benefit_line_obj = self.env['hr.payslip.benefit.line']
        benefit_lines = benefit_line_obj.search([
            ('payslip_id', 'in', payslip_ids),
            ('category_id.is_rpp_dpsp', '=', True),
        ])

        totals = {}

        for line in benefit_lines:
            reference = line.reference
            if reference not in totals:
                totals[reference] = {
                    'employer': 0,
                    'employee': 0,
                }

            totals[reference]['employee'] += (
                -line.employee_amount if line.payslip_id.credit_note
                else line.employee_amount)
            totals[reference]['employer'] += (
                -line.employer_amount if line.payslip_id.credit_note
                else line.employer_amount)

        number = ''
        max_amount = 0

        for reference in totals:
            if totals[reference]['employee'] > max_amount:
                number = reference
                max_amount = totals[reference]['employee']

        if not max_amount:
            for reference in totals:
                if totals[reference]['employer'] > max_amount:
                    number = reference
                    max_amount = totals[reference]['employer']

        return number

    @api.multi
    def get_amount(self, code=None, xml_tag=None):
        self.ensure_one()

        if code:
            if isinstance(code, (int, long)):
                code = str(code)

            amount = next(
                (a for a in self.amount_ids if a.box_id.code == code), False)
        else:
            amount = next(
                (a for a in self.amount_ids if a.box_id.xml_tag == xml_tag),
                False)

        return amount.amount if amount else False

    @api.multi
    def get_other_amount(self, index):
        self.ensure_one()

        amounts = self.other_amount_ids

        if index >= len(amounts):
            return False

        return amounts[index]

    @api.multi
    def get_other_amount_value(self, index):
        self.ensure_one()
        amount = self.get_other_amount(index)
        return amount.amount if amount else ''

    @api.multi
    def get_other_amount_code(self, index):
        self.ensure_one()
        amount = self.get_other_amount(index)
        return amount.box_id.code if amount else ''

    @api.multi
    @api.constrains('year')
    def _check_year(self):
        for slip in self:
            if not slip.year.isdigit():
                raise ValidationError(_(
                    'The year is not set properly'))
