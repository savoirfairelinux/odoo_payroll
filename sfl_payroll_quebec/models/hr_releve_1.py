# -*- coding:utf-8 -*-#########################################################
#
#    Copyright (C) 2014 Savoir-faire Linux. All Rights Reserved.
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

from openerp.osv import fields, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

from .hr_qc_summary import get_type_codes


class HrReleve1(orm.Model):
    _name = 'hr.releve_1'
    _inherit = 'hr.fiscal_slip'
    _description = 'Relevé 1'

    def set_to_draft(self, cr, uid, ids, employee_ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def button_confirm(self, cr, uid, ids, employee_ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)

    def compute_amounts(self, cr, uid, ids, context=None):
        box_obj = self.pool['hr.releve_1.box']

        for slip in self.browse(cr, uid, ids, context=context):

            slip.write({'amount_ids': [(5, 0)]})

            # Most times, a Releve 1 has either 0 or 1 child
            # Need to unlink these Releve 1, because they will
            # be recreated if required
            for child in slip.child_ids:
                child.unlink()

            slip.refresh()

            # Get all payslip of the employee for the year
            year = slip.year
            date_from = datetime(year, 1, 1).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            date_to = datetime(year, 12, 31).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            payslip_ids = self.pool['hr.payslip'].search(
                cr, uid, [
                    ('employee_id', '=', slip.employee_id.id),
                    ('date_payment', '>=', date_from),
                    ('date_payment', '<=', date_to),
                    ('state', '=', 'done'),
                ], context=context)

            # Get all types of Releve 1 box
            box_ids = box_obj.search(cr, uid, [], context=context)
            boxes = box_obj.browse(cr, uid, box_ids, context=context)

            # Create a list of all amounts to add to the slip
            amounts = []

            for box in boxes:
                box_amount = box.compute_amount(payslip_ids)

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
                slip_vals = self.copy_data(cr, uid, slip.id, context=context)

            # A Releve 1 can not have more than 4 other amounts
            # Otherwise, create a seperate Releve 1
            while(len(other_amounts) > 4):
                other_slip_id = self.create(
                    cr, uid, slip_vals, context=context)

                other_slip = self.browse(
                    cr, uid, other_slip_id, context=context)

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

        self.make_sequential_number(cr, uid, ids, context=context)
        self.make_dtmx_barcode(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'computed': True}, context=context)

    def make_sequential_number(
        self, cr, uid, ids, context=None
    ):
        for slip in self.browse(cr, uid, ids, context=context):
            # If the slip as no number, assign one
            if not slip.number:
                number = self.pool['res.company'].\
                    get_next_rq_sequential_number(
                        cr, uid, 'hr.releve_1', slip.company_id.id, slip.year,
                        context=context)

                self.write(
                    cr, uid, [slip.id], {'number': number}, context=context)

    def _dtmx_field(
        self, cr, uid, ids, value, nb_chars,
        mandatory=False, field_name=False, context=None
    ):
        """
        This function transform a unicode, int or float into
        an ascii string of a precise length

        In every case, it completes the string with spaces
        """
        # Empty fields
        if not value:
            if mandatory:
                raise orm.except_orm(
                    _('Error'), _('The field %s is missing') %
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
            raise orm.except_orm(
                _('Error'), _('The value %s is too long') % res)

        return res

    def _dtmx_address(
        self, cr, uid, ids, address, context=None
    ):

        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, 'Expected singleton'

        slip = self.browse(cr, uid, ids[0], context=context)

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

            res += slip._dtmx_field(
                value=field, nb_chars=30,
                mandatory=field_detail[1], field_name=field_detail[2])

        # Province - 2 chars
        res += slip._dtmx_field(
            address.state_id.code, 2,
            mandatory=True, field_name=_('Province'))

        # Postal Code - 6 chars
        res += slip._dtmx_field(
            address.zip, 6,
            mandatory=True, field_name=_('Zip Code'))

        return res

    def make_dtmx_barcode(self, cr, uid, ids, context=None):
        """
        Create the DataMatrix Codebar
        """
        for slip in self.browse(cr, uid, ids, context=context):
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

    def _get_other_amounts(
        self, cr, uid, ids, field_name, args=None, context=None
    ):
        """
        Get the list of amounts that will appear in the free boxes
        of the releve 1
        """
        res = {}

        for slip in self.browse(cr, uid, ids, context=context):

            other_amounts = [
                a for a in slip.amount_ids
                if a.box_id.is_other_amount
            ]

            box_o_amounts = [
                a for a in other_amounts
                if a.box_id.is_box_o_amount
            ]

            # Special case when there is exactly one other amount related
            # to Box O. The amount's code will be written directly in
            # the Box O and will not make use of the free boxes in
            # the Releve 1.
            if len(box_o_amounts) == 1:
                other_amounts = [
                    a for a in other_amounts
                    if a != box_o_amounts[0]
                ]

            res[slip.id] = [a.id for a in other_amounts]

        return res

    def _get_box_o(
        self, cr, uid, ids, field_names, args=None, context=None
    ):
        """
        The box O on the Releve 1 contains an other amount as do
        the free spaces in the bottom of the slip.

        If more than one amount is eligible to be written in box O,
        each individual amount will use a free box and the box O's code
        will be RZ to indicate that.
        """
        res = {}
        for slip in self.browse(cr, uid, ids, context=context):
            box_o_amounts = [
                a for a in slip.amount_ids
                if a.box_id.is_box_o_amount
            ]

            if len(box_o_amounts) > 1:
                # 2 amounts or more
                # The Box O will contain the sum of the amounts.
                amount = sum(a.amount for a in box_o_amounts)

                res[slip.id] = {
                    'box_o_amount': amount,
                    'box_o_amount_code': 'RZ',
                }

            elif len(box_o_amounts) == 1:
                # One amount, the box is filled with this amount
                amount = box_o_amounts[0]

                res[slip.id] = {
                    'box_o_amount': amount.amount,
                    'box_o_amount_code': amount.box_id.code,
                }

            else:
                # No amount, the box is empty
                res[slip.id] = {
                    'box_o_amount': False,
                    'box_o_amount_code': False,
                }

        return res

    _columns = {
        'slip_type': fields.selection(
            get_type_codes,
            'Type',
            required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'number': fields.integer(
            'Sequential Number',
            select=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'previous_number': fields.related(
            'amended_slip',
            'number',
            type="integer",
            string='Previous Sequential Number',
            readonly=True,
        ),
        'amended_slip': fields.many2one(
            'hr.releve_1', 'Amended Slip',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'amount_ids': fields.one2many(
            'hr.releve_1.amount',
            'slip_id',
            'Box Amounts',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'child_ids': fields.one2many(
            'hr.releve_1', 'parent_id', 'Related Releves 1',
            readonly=True, states={'draft': [('readonly', False)]},
            help="When an employee has more than 4 other amounts "
            "to be written in his Releve 1, other Releves 1 must be created."
        ),

        'parent_id': fields.many2one(
            'hr.releve_1',
            'Parent Releve 1',
            ondelete='cascade',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'summary_id': fields.many2one(
            'hr.releve_1.summary',
            'Summary',
            ondelete='cascade',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'box_o_amount': fields.function(
            _get_box_o,
            type='float',
            string='Box O Amount',
            method=True,
            multi=True,
            readonly=True,
        ),
        'box_o_amount_code': fields.function(
            _get_box_o,
            type='char',
            digits=(9, 2),
            string='Box O Amount',
            method=True,
            multi=True,
            readonly=True,
        ),
        'other_amount_ids': fields.function(
            _get_other_amounts,
            type='one2many',
            relation='hr.releve_1.amount',
            string='Other Amounts',
            method=True,
            readonly=True,
        ),

        'dtmx_barcode_string': fields.text(
            'Datamatrix String', readonly=True),

        'dtmx_barcode_image': fields.binary(
            'DataMatrix Bar Code', readonly=True),

    }
    _defaults = {
        'slip_type': 'R',
    }

    def _check_other_info(self, cr, uid, ids, context=None):
        for slip in self.browse(cr, uid, ids, context=context):

            if len(slip.other_amount_ids) > 4:
                return False

        return True

    def _check_unique_amount_type(self, cr, uid, ids, context=None):
        for slip in self.browse(cr, uid, ids, context=context):
            boxes = [a.box_id.id for a in slip.amount_ids]
            # import ipdb
            # ipdb.set_trace()
            if len(set(boxes)) != len(boxes):
                return False

        return True

    _constraints = [
        (
            _check_other_info,
            "Error. You can enter a maximum of 4 other amounts.",
            ['amount_ids']
        ),
        (
            _check_unique_amount_type,
            "Error. For each amount, the source must be different.",
            ['amount_ids']
        ),
    ]

    def name_get(self, cr, uid, ids, context=None):
        return [
            (slip.id, "%s - %s - %s" % (
                slip.employee_id.name, slip.year, slip.number))
            for slip in self.browse(cr, uid, ids, context=context)
        ]

    def get_other_amount_code(self, cr, uid, ids, index, context=None):
        """
        Override the method get_other_amount_code from hr.fiscal_slip
        so that it adds RZ- before the code if the amount is related to
        the releve 1 box O.
        """
        amount = self.get_other_amount(cr, uid, ids, index, context=context)

        if not amount:
            return ''

        box = amount.box_id

        return 'RZ-%s' % box.code if box.is_box_o_amount else box.code
