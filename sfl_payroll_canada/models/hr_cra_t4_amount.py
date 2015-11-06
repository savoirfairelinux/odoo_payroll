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
import openerp.addons.decimal_precision as dp


class HrCRAT4Amount(orm.Model):
    _name = 'hr.cra.t4.amount'
    _description = 'CRA T4 Amount'

    _columns = {
        'slip_id': fields.many2one(
            'hr.cra.t4', 'T4 Slip', required=True, ondelete='cascade',
        ),
        'box_id': fields.many2one(
            'hr.cra.t4.box', 'T4 Box', required=True,
        ),
        'amount': fields.float(
            'Amount',
            digits_compute=dp.get_precision('Payroll'),
            required=True,
        ),
        'is_other_amount': fields.related(
            'box_id',
            'is_other_amount',
            type='boolean',
            string='Is Other Amount',
            readonly=True,
        ),
        'code': fields.related(
            'box_id',
            'code',
            type='char',
            string='Code',
            readonly=True,
        ),
        'xml_tag': fields.related(
            'box_id',
            'xml_tag',
            type='char',
            string='XML Tag',
            readonly=True,
        ),
    }

    _order = 'box_id'
