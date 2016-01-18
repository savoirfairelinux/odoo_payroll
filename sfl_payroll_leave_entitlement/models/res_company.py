# -*- coding:utf-8 -*-
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

from itertools import permutations

from openerp.osv import fields, orm


class ResCompany(orm.Model):
    _inherit = 'res.company'
    _columns = {
        'week_start': fields.selection(
            [
                ('0', 'Sunday'),
                ('1', 'Monday'),
                ('2', 'Tuesday'),
                ('3', 'Wednesday'),
                ('4', 'Thursday'),
                ('5', 'Friday'),
                ('6', 'Saturday'),
            ],
            string="Week start",
            type="char",
        ),
        'holidays_entitlement_ids': fields.many2many(
            'hr.holidays.entitlement',
            'res_company_holidays_entitlement_rel',
            string='Leave Entitlement Periods',
        ),
    }

    _defaults = {
        'week_start': '0',
    }

    def _check_leave_entitlement(
        self, cr, uid, ids, context=None
    ):
        """
        Check that the employee has maximum one leave entitlement
        per leave type
        """
        for contract in self.browse(cr, uid, ids, context=context):
            for e1, e2 in permutations(contract.holidays_entitlement_ids, 2):
                if e1.leave_id == e2.leave_id:
                    return False

        return True

    _constraints = [
        (
            _check_leave_entitlement,
            "A company can not have more than one holidays entitlement "
            "per leave type.",
            ['holidays_entitlement_ids']
        ),
    ]
