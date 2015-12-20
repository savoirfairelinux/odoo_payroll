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


class HrReleve1Amount(orm.Model):
    _name = 'hr.releve_1.amount'
    _description = 'Releve 1 Amount'

    _columns = {
        'slip_id': fields.many2one(
            'hr.releve_1', 'Releve 1', required=True, ondelete='cascade',
        ),
        'box_id': fields.many2one(
            'hr.releve_1.box', 'Fiscal Slip Box', required=True,
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
            store=True,
            string='Is Other Amount'
        ),
        'is_box_o_amount': fields.related(
            'box_id',
            'is_box_o_amount',
            type='boolean',
            store=True,
            string='Is Box O Revenue'
        ),
    }
