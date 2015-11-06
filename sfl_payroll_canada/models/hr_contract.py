# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
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

from openerp.osv import fields, orm


class HrContract(orm.Model):
    _inherit = 'hr.contract'

    def _get_hourly_rate_from_wage(
        self, cr, uid, ids, field_name, arg=None, context=None
    ):
        """
        :param ids: ID of contract
        :return: The hourly rate computed from the wage of an employee.
        """
        res = {}
        for contract in self.browse(cr, uid, ids, context=context):
            res[contract.id] = contract.wage / (
                contract.pays_per_year * contract.worked_hours_per_pay_period
            )
        return res

    _columns = {
        'weeks_of_vacation': fields.float(
            'Number of weeks of vacation',
        ),
        'worked_hours_per_pay_period': fields.float(
            'Worked Hours per Pay Period',
        ),
        'hourly_rate_from_wage': fields.function(
            _get_hourly_rate_from_wage,
            type="float",
            method=True,
            string="Estimated Hourly Rate",
        ),
    }

    _defaults = {
        'weeks_of_vacation': 2,
        'worked_hours_per_pay_period': 40,
    }
