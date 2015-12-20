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


class HrReleve1SummaryBox(orm.Model):
    _name = 'hr.releve_1.summary.box'
    _description = 'Releve 1 Summary Box'

    _columns = {
        'name': fields.char('Name', required=True),
        'active': fields.boolean('Active'),
        'child_ids': fields.many2many(
            'hr.releve_1.box',
            'hr_releve_1_summary_total_box_rel',
            string='Related Releve 1 Boxes that will be summed in the'
            'Summary Box.',
        ),
    }

    _defaults = {
        'active': True,
    }

    def compute_amount(self, cr, uid, ids, slip_ids, context=None):
        """
        Return the amount of a Releve 1 Summary box from the given
        list of slips related to the summary

        :type slip_ids: hr.releve_1 id list
        :rtype: float
        """

        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1

        child_amount_model = self.pool['hr.releve_1.amount']

        box = self.browse(cr, uid, ids[0], context=context)
        child_ids = [b.id for b in box.child_ids]

        amount_ids = child_amount_model.search(cr, uid, [
            ('slip_id', 'in', slip_ids),
            ('box_id', 'in', child_ids),
        ], context=context)

        amounts = child_amount_model.browse(
            cr, uid, amount_ids, context=context)

        return sum(a.amount for a in amounts)
