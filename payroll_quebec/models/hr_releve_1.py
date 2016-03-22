# -*- coding:utf-8 -*-#########################################################
#
#    Copyright (C) 2016 Savoir-faire Linux. All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by
#    the Free Software Foundation, either version 3 of the License, or
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

import base64
import os
import unicodedata

from datetime import datetime
from elaphe.datamatrix import DataMatrix

from openerp import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError

from .hr_qc_summary import get_type_codes


class HrReleve1(models.Model):
    """Relevé 1"""

    _name = 'hr.releve_1'
    _inherit = 'hr.fiscal_slip'
    _description = _(__doc__)

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def button_confirm(self):
        self.write({'state': 'confirmed'})

    @api.multi
    def compute_amounts(self):
        self.write({'amount_ids': [(5, 0)]})
        # Most times, a Releve 1 has either 0 or 1 child
        # Need to unlink these Releve 1, because they will
        # be recreated if required
        self.mapped('child_ids').unlink()
        self.refresh()

        for slip in self:
            # Get all payslip of the employee for the year
            year = int(slip.year)
            date_from = datetime(year, 1, 1).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            date_to = datetime(year, 12, 31).strftime(
                DEFAULT_SERVER_DATE_FORMAT)

            payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('date_payment', '>=', date_from),
                ('date_payment', '<=', date_to),
                ('state', '=', 'done'),
            ])

            # Get all types of Releve 1 box
            boxes = self.env['hr.releve_1.box'].search([])

            # Create a list of all amounts to add to the slip
            amounts = []

            for box in boxes:
                box_amount = box.compute_amount(payslips.ids)

                if box_amount or box.required:
                    amounts.append({
                        'amount': box_amount,
                        'box_id': box.id,
                        'is_other_amount': box.is_other_amount,
                        'is_box_o_amount': box.is_box_o_amount,
                    })

            slip.refresh()

            std_amounts = [
                a for a in amounts if not a['is_other_amount']
            ]

            other_amounts = [
                a for a in amounts if a['is_other_amount']
            ]

            box_o_amounts = [
                a for a in other_amounts if a['is_box_o_amount']
            ]

            if len(box_o_amounts) == 1:
                other_amounts = [
                    a for a in other_amounts if a != box_o_amounts[0]
                ]

                std_amounts.append(box_o_amounts[0])

            else:
                # Get box O amounts at the beginning of the other amounts
                # so that they will likely be all written to the same Releve 1
                other_amounts.sort(key=lambda a: not a['is_box_o_amount'])

            slip.write({'computed': True})

            if len(other_amounts) > 4:
                slip_vals = slip.copy_data()

            # A Releve 1 can not have more than 4 other amounts
            # Otherwise, create a seperate Releve 1
            while(len(other_amounts) > 4):
                other_slip = self.create(slip_vals)

                other_slip.write({
                    'amount_ids': [
                        (0, 0, amount) for amount in other_amounts[4:8]
                    ],
                    'parent_id': slip.id,
                })

                other_slip.refresh()

                other_slip_boxes = [
                    a.box_id for a in other_slip.amount_ids
                ]

                # Add the missing mandatory boxes to the slip
                required_boxes = [
                    b for b in boxes
                    if b.required and b not in other_slip_boxes
                ]

                other_slip.write({
                    'amount_ids': [
                        (0, 0, {
                            'box_id': b.id,
                            'amount': 0,
                        }) for b in required_boxes
                    ],
                })

                other_amounts = other_amounts[0:4] + other_amounts[8:]

            slip.write({
                'amount_ids': [
                    (0, 0, amount) for amount in std_amounts + other_amounts
                ]
            })

        self.make_sequential_number()
        self.make_dtmx_barcode()
        self.write({'computed': True})

    @api.multi
    def make_sequential_number(self):
        for slip in self:
            # If the slip as no number, assign one
            if not slip.number:
                number = self.company_id.get_next_rq_sequential_number(
                    'hr.releve_1', int(slip.year))

                self.write({'number': number})

    @api.model
    def _dtmx_field(self, value, nb_chars, mandatory=False, field_name=False):
        """
        This function transform a unicode, int or float into
        an ascii string of a precise length

        In every case, it completes the string with spaces
        """
        # Empty fields
        if not value:
            if mandatory:
                raise ValidationError(
                    _('The field %s is missing') %
                    field_name,
                )
            res = ' ' * nb_chars

        # Floats: removes the floating point but keeps every digit
        # Adds spaces before the string
        elif isinstance(value, float):
            value = str(int(value * 100))
            res = "%s%s" % (' ' * (nb_chars - len(value)), value)

        # Integers: the same logic as with floats
        elif isinstance(value, (int, long)):
            value = str(value)
            res = "%s%s" % (' ' * (nb_chars - len(value)), value)

        # Unicode: converts to ascii and adds missing spaces after
        else:
            value = unicodedata.normalize(
                'NFKD', unicode(value)
            ).encode('ascii', 'ignore')
            res = "%s%s" % (value, ' ' * (nb_chars - len(value)),)

        # We check that the field is the proper size
        if len(res) > nb_chars:
            raise ValidationError(
                _('The value %s is too long') % res)

        return res

    @api.multi
    def _dtmx_address(self, address):
        self.ensure_one()

        res = ""

        # 3 fields of 30 chars
        for field_detail in [
            (address.street, True, _('Street Line 1')),
            (address.street2, False, _('Street Line 2')),
            (address.city, True, _('City')),
        ]:
            # Get the first 30 chars of the field
            field = field_detail[0]
            field = field and field[0:30]

            res += self._dtmx_field(
                value=field, nb_chars=30,
                mandatory=field_detail[1], field_name=field_detail[2])

        # Province - 2 chars
        res += self._dtmx_field(
            address.state_id.code, 2,
            mandatory=True, field_name=_('Province'))

        # Postal Code - 6 chars
        res += self._dtmx_field(
            address.zip, 6,
            mandatory=True, field_name=_('Zip Code'))

        return res

    @api.multi
    def make_dtmx_barcode(self):
        """
        Create the DataMatrix Codebar
        """
        for slip in self:
            slip.employee_id.check_personal_info()

            # Code related to the slip type
            dtmx_string = slip._dtmx_field("12EE", nb_chars=4)

            # Authorization number
            dtmx_string += slip._dtmx_field("FS9999999", nb_chars=9)

            dtmx_string += slip._dtmx_field(
                slip.company_id.rq_preparator_number, 8,
                field_name=_("Preparator Number"))

            dtmx_string += slip._dtmx_field(slip.year, nb_chars=4)

            dtmx_string += slip._dtmx_field(slip.slip_type, nb_chars=1)

            dtmx_string += slip._dtmx_field(
                slip.previous_number, nb_chars=9)

            dtmx_string += slip._dtmx_field(slip.reference, nb_chars=9)

            dtmx_string += slip._dtmx_field(slip.number, nb_chars=9)

            std_amounts = {
                a.box_id.code: a.amount
                for a in slip.amount_ids if not a.is_other_amount
            }

            # amounts - 9 chars
            for field in [
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                'M', 'N',
            ]:
                dtmx_string += slip._dtmx_field(
                    std_amounts.get(field, False), nb_chars=9)

            dtmx_string += slip._dtmx_field(slip.box_o_amount, nb_chars=9)

            # amounts - 9 chars
            for field in ['P', 'Q', 'R', 'S']:
                dtmx_string += slip._dtmx_field(
                    std_amounts.get(field, False), nb_chars=9)

            # P if tip earned - 1 char
            dtmx_string += 'P' if std_amounts.get('S') else ' '

            for field in ['T', 'U', 'V', 'W']:
                dtmx_string += slip._dtmx_field(
                    std_amounts.get(field, False), nb_chars=9)

            dtmx_string += slip._dtmx_field(
                slip.box_o_amount_code, nb_chars=2)

            dtmx_string += slip._dtmx_field(
                int(slip.employee_id.sin), nb_chars=9)

            # Reference Number (not mandatory) - 20 chars
            dtmx_string += slip._dtmx_field(slip.reference, nb_chars=20)

            employee = slip.employee_id

            for field_detail in [
                (employee.lastname, True, _('Last Name')),
                (employee.firstname, True, _('First Name')),
            ]:
                # Get the first 30 chars of the field
                field = field_detail[0]
                field = field and field[0:30]

                dtmx_string += slip._dtmx_field(
                    value=field, nb_chars=30,
                    mandatory=field_detail[1], field_name=field_detail[2])

            dtmx_string += slip._dtmx_address(employee.address_home_id)

            # company name - 60 chars
            dtmx_string += slip._dtmx_field(
                value=slip.company_id.name, nb_chars=60)

            # Company address
            dtmx_string += slip._dtmx_address(slip.company_id)

            other_amounts = slip.other_amount_ids

            # Loop for every additional information
            for i in range(0, 4):
                if other_amounts and len(other_amounts) > i:

                    amount = other_amounts[i]

                    # Write the source and the amount
                    dtmx_string += slip._dtmx_field(amount.box_id.code, 5)
                    dtmx_string += slip._dtmx_field(amount.amount, 15)

                else:
                    dtmx_string += slip._dtmx_field(False, 20)

            # Make DataMatrix image
            dtmx_obj = DataMatrix()
            dtmx_pil_img = dtmx_obj.render(dtmx_string)

            # Put the datamatrix image in a temp file
            directory = os.path.join('/tmp')
            if not os.path.isdir(directory):
                os.makedirs(directory)

            filename = directory + '/releve_1_datamatrix_code.jpg'
            dtmx_pil_img.save(filename, 'JPEG')

            # Get a binary field by decoding the temp file
            b64_data = base64.encodestring(open(filename, "rb").read())

            slip.write({
                'dtmx_barcode_string': dtmx_string,
                'dtmx_barcode_image': b64_data,
            })

            # Remove the temp file
            os.remove(filename)

    def _get_other_amounts(self):
        """
        Get the list of amounts that will appear in the free boxes
        of the releve 1
        """
        for slip in self:
            other_amounts = slip.amount_ids.filtered(
                lambda a: a.box_id.is_other_amount)

            box_o_amounts = other_amounts.filtered(
                lambda a: a.box_id.is_box_o_amount)

            # Special case when there is exactly one other amount related
            # to Box O. The amount's code will be written directly in
            # the Box O and will not make use of the free boxes in
            # the Releve 1.
            if len(box_o_amounts) == 1:
                other_amounts = other_amounts.filtered(
                    lambda a: a != box_o_amounts[0])

            slip.other_amount_ids = other_amounts.ids

    def _get_box_o(self):
        """
        The box O on the Releve 1 contains an other amount as do
        the free spaces in the bottom of the slip.

        If more than one amount is eligible to be written in box O,
        each individual amount will use a free box and the box O's code
        will be RZ to indicate that.
        """
        for slip in self:
            box_o_amounts = slip.amount_ids.filtered(
                lambda a: a.box_id.is_box_o_amount)

            if len(box_o_amounts) > 1:
                # 2 amounts or more
                # The Box O will contain the sum of the amounts.
                amount = sum(a.amount for a in box_o_amounts)

                slip.box_o_amount = amount
                slip.box_o_amount_code = 'RZ'

            elif len(box_o_amounts) == 1:
                # One amount, the box is filled with this amount
                amount = box_o_amounts[0]

                slip.box_o_amount = amount.amount
                slip.box_o_amount_code = amount.box_id.code

            else:
                # No amount, the box is empty
                slip.box_o_amount = False
                slip.box_o_amount_code = False

    slip_type = fields.Selection(
        get_type_codes,
        'Type',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default='R',
    )
    number = fields.Integer(
        'Sequential Number',
        select=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    previous_number = fields.Integer(
        'Previous Sequential Number',
        related='amended_slip.number',
        readonly=True,
    )
    amended_slip = fields.Many2one(
        'hr.releve_1', 'Amended Slip',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    amount_ids = fields.One2many(
        'hr.releve_1.amount',
        'slip_id',
        'Box Amounts',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    child_ids = fields.One2many(
        'hr.releve_1', 'parent_id', 'Related Releves 1',
        readonly=True, states={'draft': [('readonly', False)]},
        help="When an employee has more than 4 other amounts "
        "to be written in his Releve 1, other Releves 1 must be created."
    )

    parent_id = fields.Many2one(
        'hr.releve_1',
        'Parent Releve 1',
        ondelete='cascade',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    summary_id = fields.Many2one(
        'hr.releve_1.summary',
        'Summary',
        ondelete='cascade',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    box_o_amount = fields.Float(
        compute='_get_box_o',
        string='Box O Amount',
        readonly=True,
        digits_compute=dp.get_precision('Payroll'),
    )
    box_o_amount_code = fields.Char(
        compute='_get_box_o',
        string='Box O Amount',
        readonly=True,
    )
    other_amount_ids = fields.One2many(
        'hr.releve_1.amount',
        'slip_id',
        'Other Amounts',
        compute='_get_other_amounts',
        readonly=True,
    )

    dtmx_barcode_string = fields.Text(
        'Datamatrix String', readonly=True
    )

    dtmx_barcode_image = fields.Binary(
        'DataMatrix Bar Code', readonly=True
    )

    @api.multi
    @api.constrains('amount_ids')
    def _check_other_info(self):
        for slip in self:
            if len(slip.other_amount_ids) > 4:
                raise ValidationError(_(
                    "Error. You can enter a maximum of 4 other amounts."
                ))

        return True

    @api.multi
    @api.constrains('amount_ids')
    def _check_unique_amount_type(self):
        for slip in self:
            boxes = slip.mapped('amount_ids.box_id')
            # import ipdb
            # ipdb.set_trace()
            if len(slip.amount_ids) != len(boxes):
                raise ValidationError(_(
                    "Error. For each amount, the source must be different."
                ))

        return True

    @api.multi
    def name_get(self):
        return [
            (slip.id, "%s - %s - %s" % (
                slip.employee_id.name, slip.year, slip.number))
            for slip in self
        ]

    @api.multi
    def get_other_amount_code(self, index):
        """
        Override the method get_other_amount_code from hr.fiscal_slip
        so that it adds RZ- before the code if the amount is related to
        the releve 1 box O.
        """
        self.ensure_one()
        amount = self.get_other_amount(index)

        if not amount:
            return ''

        box = amount.box_id

        return 'RZ-%s' % box.code if box.is_box_o_amount else box.code
