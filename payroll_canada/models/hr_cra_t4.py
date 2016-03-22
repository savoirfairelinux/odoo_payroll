# -*- coding:utf-8 -*-char(

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

from datetime import datetime, date

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

to_string = fields.Date.to_string


class HrCraT4(models.Model):
    """T4 Slip"""

    _name = 'hr.cra.t4'
    _inherit = 'hr.cra.fiscal_slip'
    _description = _(__doc__)

    name = fields.Char(
        'Name', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'hr.cra.t4')
    )
    rpp_dpsp_rgst_nbr = fields.Integer(
        'RPP/PRPP registration number',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    cpp_qpp_xmpt_cd = fields.Boolean(
        'CPP or QPP exempt',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    ei_xmpt_cd = fields.Boolean(
        'Employment Insurance exempt',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    prov_pip_xmpt_cd = fields.Boolean(
        'Provincial parental insurance plan exempt',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    empt_cd = fields.Char(
        'Employment code',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    amount_ids = fields.One2many(
        'hr.cra.t4.amount',
        'slip_id',
        'Box Amounts',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    other_amount_ids = fields.One2many(
        'hr.cra.t4.amount',
        'slip_id',
        domain=[('is_other_amount', '=', True)],
        string='Other Amounts',
    )

    child_ids = fields.One2many(
        'hr.cra.t4', 'parent_id', 'Related T4 Slips',
        readonly=True, states={'draft': [('readonly', False)]},
        help="When an employee has more than 6 other amounts "
        "to be written in his T4 slip, other T4 slips must be created."
    )

    parent_id = fields.Many2one(
        'hr.cra.t4',
        'Parent T4',
        ondelete='cascade',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    summary_id = fields.Many2one(
        'hr.cra.t4.summary',
        'Summary',
        ondelete='cascade',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    @api.one
    @api.constrains('amount_ids')
    def _check_amounts(self):
        # Check that their is maximum 6 amounts
        if len(self.other_amount_ids) > 6:
            raise ValidationError(
                'You can enter a maximum of 6 other amounts.'
            )

        # For each amount, the source must be different
        boxes = [a.box_id for a in self.amount_ids]
        if len(set(boxes)) != len(boxes):
            raise ValidationError(
                'All amounts must be different from each other.'
            )

        return True

    @api.multi
    def button_set_to_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def button_confirm(self):
        self.write({'state': 'confirmed'})

    @api.one
    def compute_amounts(self):
        self.write({'amount_ids': [(5, 0)]})

        # Most times, a T4 has either 0 or 1 child
        # Need to unlink these T4, because they will
        # be recreated if required
        self.child_ids.unlink()
        self.refresh()

        # Get all payslip of the employee for the year
        year = int(self.year)

        date_from = to_string(datetime(year, 1, 1))
        date_to = to_string(datetime(year, 12, 31))

        payslip_ids = self.env['hr.payslip'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date_payment', '>=', date_from),
            ('date_payment', '<=', date_to),
            ('state', '=', 'done'),
        ]).ids

        # Get all types of t4 box
        boxes = self.env['hr.cra.t4.box'].search([])

        # Create a list of all amounts to add to the slip
        amounts = []

        for box in boxes:
            box_amount = box.compute_amount(payslip_ids)

            if box_amount or box.required:
                amounts.append({
                    'amount': box_amount,
                    'box_id': box.id,
                    'is_other_amount': box.is_other_amount,
                })

        std_amounts = [
            a for a in amounts if not a['is_other_amount']
        ]

        other_amounts = [
            a for a in amounts if a['is_other_amount']
        ]

        self.refresh()

        employee = self.employee_id
        year_end = date(int(self.year), 12, 31).strftime(
            DEFAULT_SERVER_DATE_FORMAT)

        def get_t4_amount(ref):
            box_id = self.env.ref('payroll_canada.%s' % ref).id
            return next((
                a.amount for a in amounts if a['box_id'] == box_id), False)

        # T4 vals
        self.write({
            'ei_xmpt_cd': employee.exempted_from('CA_EI', year_end) and
            not get_t4_amount('t4_box_empe_eip_amt'),
            'cpp_qpp_xmpt_cd': employee.exempted_from('CA_CPP', year_end) and
            not get_t4_amount('t4_box_cpp_cntrb_amt') and
            not get_t4_amount('t4_box_qpp_cntrb_amt'),
            'prov_pip_xmpt_cd': employee.exempted_from('CA_PIP', year_end) and
            not get_t4_amount('t4_box_prov_pip_amt')
        })

        rpp_dpsp_rgst_nbr = self.get_rpp_dpsp_rgst_nbr(payslip_ids)

        if rpp_dpsp_rgst_nbr:
            self.write({'rpp_dpsp_rgst_nbr': rpp_dpsp_rgst_nbr})

        self.write({'computed': True})

        if len(other_amounts) > 6:
            slip_vals = self.copy_data()[0]

        # A T4 can not have more than 6 other amounts
        # Otherwise, create a seperate T4
        while(len(other_amounts) > 6):
            other_slip = self.create(slip_vals)

            other_slip.write({
                'amount_ids': [
                    (0, 0, amount) for amount in other_amounts[6:12]
                ],
                'parent_id': self.id,
            })

            other_slip.refresh()

            other_slip_boxes = other_slip.amount_ids.mapped('box_id')

            # Add the missing mandatory boxes to the slip
            required_boxes = boxes.filtered(
                lambda b: b.required and b not in other_slip_boxes
            )

            other_slip.write({
                'amount_ids': [
                    (0, 0, {
                        'box_id': b.id,
                        'amount': 0,
                    }) for b in required_boxes
                ],
            })

            other_amounts = other_amounts[0:6] + other_amounts[12:]

        self.write({
            'amount_ids': [
                (0, 0, amount) for amount in std_amounts + other_amounts
            ]
        })
