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

from openerp.osv import orm, fields


class HrCRAT4SummaryBox(orm.Model):
    _name = 'hr.cra.t4.summary.box'
    _description = 'T4 Summary Box'

    _columns = {
        'name': fields.char('Name', required=True),
        'active': fields.boolean('Active'),
        'xml_tag': fields.char('XML Tag', required=True),
        'child_ids': fields.many2many(
            'hr.cra.t4.box',
            'hr_t4_summary_total_box_rel',
            string='Related T4 Boxes',
        ),
    }

    _defaults = {
        'active': True,
    }

    def compute_amount(self, cr, uid, ids, slip_ids, context=None):
        """
        Return the amount of a T4 Summary box from the given
        list of slips related to the summary

        :type slip_ids: hr.cra.t4 id list
        :rtype: float
        """

        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, "Expected single record"

        child_amount_model = self.pool['hr.cra.t4.amount']

        box = self.browse(cr, uid, ids[0], context=context)
        child_box_ids = [b.id for b in box.child_ids]

        child_amount_ids = child_amount_model.search(cr, uid, [
            ('slip_id', 'in', slip_ids),
            ('box_id', 'in', child_box_ids),
        ], context=context)

        child_amounts = child_amount_model.browse(
            cr, uid, child_amount_ids, context=context)

        return sum(a.amount for a in child_amounts)
