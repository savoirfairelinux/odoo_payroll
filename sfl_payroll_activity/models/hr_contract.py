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

from openerp import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def _get_hourly_rate_from_wage(self):
        """
        :param ids: ID of contract
        :return: The hourly rate computed from the wage of an employee.
        """
        for contract in self:
            contract.hourly_rate_from_wage = contract.wage / (
                contract.pays_per_year * contract.worked_hours_per_pay_period
            )

    weeks_of_vacation = fields.Float(
        'Number of weeks of vacation',
        default=2,
    )
    worked_hours_per_pay_period = fields.Float(
        'Worked Hours per Pay Period',
        default=40,
    )
    hourly_rate_from_wage = fields.Float(
        "Estimated Hourly Rate",
        compute='_get_hourly_rate_from_wage',
        readonly=True,
    )
