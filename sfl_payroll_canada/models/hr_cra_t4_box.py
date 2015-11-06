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


class HrCRAT4Box(orm.Model):
    _name = 'hr.cra.t4.box'
    _inherits = {'hr.fiscal_slip.box': 'fiscal_slip_box_id'}
    _description = 'CRA T4 Box'

    _columns = {
        'fiscal_slip_box_id': fields.many2one(
            'hr.fiscal_slip.box', 'Fiscal Slip Box',
            required=True, ondelete='cascade',
        ),
    }

    def compute_amount(self, cr, uid, ids, payslip_ids, context=None):

        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, "Expected single record"

        box = self.browse(cr, uid, ids[0], context=context)

        return box.fiscal_slip_box_id.compute_amount(payslip_ids)
