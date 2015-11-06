# -*- coding:utf-8 -*-char(

##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
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

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class HrCraT4(orm.Model):
    _name = 'hr.cra.t4'
    _inherit = 'hr.cra.fiscal_slip'
    _description = 'T4 Slip'

    def _get_other_amounts(
        self, cr, uid, ids, field_name, args=None, context=None
    ):
        """
        Get the list of amounts that will appear in the free boxes
        of the releve 1
        """
        res = {}

        for slip in self.browse(cr, uid, ids, context=context):

            res[slip.id] = [
                a.id for a in slip.amount_ids if a.box_id.is_other_amount
            ]

        return res

    _columns = {
        'name': fields.char(
            'Name', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'rpp_dpsp_rgst_nbr': fields.integer(
            'RPP/PRPP registration number',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'cpp_qpp_xmpt_cd': fields.boolean(
            'CPP or QPP exempt',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'ei_xmpt_cd': fields.boolean(
            'Employment Insurance exempt',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'prov_pip_xmpt_cd': fields.boolean(
            'Provincial parental insurance plan exempt',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'empt_cd': fields.char(
            'Employment code',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'amount_ids': fields.one2many(
            'hr.cra.t4.amount',
            'slip_id',
            'Box Amounts',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'other_amount_ids': fields.function(
            _get_other_amounts,
            type='one2many',
            string='Other Amounts',
            method=True,
            relation="hr.cra.t4.amount",
        ),

        'child_ids': fields.one2many(
            'hr.cra.t4', 'parent_id', 'Related T4 Slips',
            readonly=True, states={'draft': [('readonly', False)]},
            help="When an employee has more than 6 other amounts "
            "to be written in his T4 slip, other T4 slips must be created."
        ),

        'parent_id': fields.many2one(
            'hr.cra.t4',
            'Parent T4',
            ondelete='cascade',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'summary_id': fields.many2one(
            'hr.cra.t4.summary',
            'Summary',
            ondelete='cascade',
            readonly=True, states={'draft': [('readonly', False)]},
        ),
    }

    def _check_amounts(self, cr, uid, ids, context=None):
        for slip in self.browse(cr, uid, ids, context=context):

            other_amounts = [a for a in slip.amount_ids if a.is_other_amount]

            # Check that their is maximum 6 amounts
            if len(other_amounts) > 6:
                return False

            # For each amount, the source must be different
            boxes = [a.box_id for a in slip.amount_ids]
            if len(set(boxes)) != len(boxes):
                return False

        return True

    _constraints = [
        (
            _check_amounts,
            "Error! You can enter a maximum of 6 other amounts "
            "and all amounts must be different from each other.",
            ['amount_ids']
        ),
    ]

    _defaults = {
        'name': lambda self, cr, uid, c={}:
        self.pool['ir.sequence'].get(cr, uid, 'hr.cra.t4'),
    }

    def button_set_to_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def button_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)

    def compute_amounts(
        self, cr, uid, ids, context=None
    ):
        box_obj = self.pool['hr.cra.t4.box']
        data_obj = self.pool['ir.model.data']

        for slip in self.browse(cr, uid, ids, context=context):

            slip.write({'amount_ids': [(5, 0)]})

            # Most times, a T4 has either 0 or 1 child
            # Need to unlink these T4, because they will
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

            # Get all types of t4 box
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
                    })

            std_amounts = [
                a for a in amounts if not a['is_other_amount']
            ]

            other_amounts = [
                a for a in amounts if a['is_other_amount']
            ]

            slip.refresh()

            employee = slip.employee_id
            year_end = date(slip.year, 12, 31).strftime(
                DEFAULT_SERVER_DATE_FORMAT)

            def get_t4_amount(ref):
                box_id = data_obj(cr, uid, 'sfl_payroll_canada', ref)[1]
                return next((
                    a.amount for a in amounts if a['box_id'] == box_id), False)

            # T4 vals
            slip.write({
                'ei_xmpt_cd': employee.exempted_from('CA_EI', year_end)
                and not get_t4_amount('t4_box_empe_eip_amt'),
                'cpp_qpp_xmpt_cd': employee.exempted_from('CA_CPP', year_end)
                and not get_t4_amount('t4_box_cpp_cntrb_amt')
                and not get_t4_amount('t4_box_qpp_cntrb_amt'),
                'prov_pip_xmpt_cd': employee.exempted_from('CA_PIP', year_end)
                and not get_t4_amount('t4_box_prov_pip_amt')
            })

            rpp_dpsp_rgst_nbr = self.get_rpp_dpsp_rgst_nbr(
                cr, uid, payslip_ids, context=context)

            if rpp_dpsp_rgst_nbr:
                slip.write({'rpp_dpsp_rgst_nbr': rpp_dpsp_rgst_nbr})

            slip.write({'computed': True})

            if len(other_amounts) > 6:
                slip_vals = self.copy_data(cr, uid, slip.id, context=context)

            # A T4 can not have more than 6 other amounts
            # Otherwise, create a seperate T4
            while(len(other_amounts) > 6):
                other_slip_id = self.create(
                    cr, uid, slip_vals, context=context)

                other_slip = self.browse(
                    cr, uid, other_slip_id, context=context)

                other_slip.write({
                    'amount_ids': [
                        (0, 0, amount) for amount in other_amounts[6:12]
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

                other_amounts = other_amounts[0:6] + other_amounts[12:]

            slip.write({
                'amount_ids': [
                    (0, 0, amount) for amount in std_amounts + other_amounts
                ]
            })
