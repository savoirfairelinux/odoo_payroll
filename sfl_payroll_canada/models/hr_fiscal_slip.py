# -*- coding:utf-8 -*-
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

import time

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _


def get_states(self, cr, uid, context=None):
    return [
        ('cancelled', _('Cancelled')),
        ('draft', _('Draft')),
        ('confirmed', _('Confirmed')),
        ('sent', _('Sent')),
    ]


class HrFiscalSlip(orm.AbstractModel):
    """
    This model contains every standard fields on an employee's fiscal slip
    in Canada
    """
    _name = 'hr.fiscal_slip'
    _description = 'Fiscal Slip'

    _columns = {
        'company_id': fields.many2one(
            'res.company',
            'Company',
            required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'address_home_id': fields.related(
            'employee_id',
            'address_home_id',
            string='Home Address',
            type="many2one",
            relation="res.partner",
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'reference': fields.char(
            'Reference',
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'year': fields.integer(
            'Fiscal Year',
            required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'state': fields.selection(
            get_states,
            'Status',
            type='char',
            select=True,
            required=True,
        ),
        'employee_id': fields.many2one(
            'hr.employee',
            'Employee',
            required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'computed': fields.boolean(
            'Computed',
            readonly=True, states={'draft': [('readonly', False)]},
        ),
    }

    _defaults = {
        'state': 'draft',
        'company_id': lambda self, cr, uid, context:
        self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id,
        'year': lambda *a: int(time.strftime(
            DEFAULT_SERVER_DATE_FORMAT)[0:4]) - 1,
    }

    def get_rpp_dpsp_rgst_nbr(self, cr, uid, payslip_ids, context=None):
        """
        Find the RPP/DPSP registration number with the highest amount
        contributed in a list of payslips

        If the employee contributed, return the number with highest
        employee contribution, otherwise the highest employer contribution
        """
        benefit_line_obj = self.pool['hr.payslip.benefit.line']
        benefit_line_ids = benefit_line_obj.search(cr, uid, [
            ('payslip_id', 'in', payslip_ids),
            ('category_id.is_rpp_dpsp', '=', True),
        ], context=context)

        benefit_lines = benefit_line_obj.browse(
            cr, uid, benefit_line_ids, context=context)

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

    def get_amount(self, cr, uid, ids, code=None, xml_tag=None, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, "Expected single record"

        slip = self.browse(cr, uid, ids[0], context=context)

        if code:
            if isinstance(code, (int, long)):
                code = str(code)

            amount = next(
                (a for a in slip.amount_ids if a.box_id.code == code), False)
        else:
            amount = next(
                (a for a in slip.amount_ids if a.box_id.xml_tag == xml_tag),
                False)

        return amount.amount if amount else False

    def get_other_amount(self, cr, uid, ids, index, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, "Expected single record"

        slip = self.browse(cr, uid, ids[0], context=context)

        amounts = slip.other_amount_ids

        if index >= len(amounts):
            return False

        return amounts[index]

    def get_other_amount_value(self, cr, uid, ids, index, context=None):
        amount = self.get_other_amount(cr, uid, ids, index, context=context)
        return amount.amount if amount else ''

    def get_other_amount_code(self, cr, uid, ids, index, context=None):
        amount = self.get_other_amount(cr, uid, ids, index, context=context)
        return amount.box_id.code if amount else ''
