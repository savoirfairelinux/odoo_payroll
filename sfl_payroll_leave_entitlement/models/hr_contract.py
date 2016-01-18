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

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrContract(models.Model):

    _inherit = 'hr.contract'

    holidays_entitlement_ids = fields.Many2many(
        'hr.holidays.entitlement',
        'hr_contract_holidays_entitlement_rel',
        string='Leave Entitlement Periods',
    )

    @api.one
    @api.constrains('holidays_entitlement_ids')
    def _check_leave_entitlement(self):
        """
        Check that the employee has maximum one leave entitlement
        per leave type
        """
        for e1, e2 in permutations(self.holidays_entitlement_ids, 2):
            if e1.leave_id == e2.leave_id:
                return ValidationError(
                    "A contract can not have more than one holidays "
                    "entitlement per leave type.")

    @api.multi
    @api.returns('hr.holidays.entitlement')
    def get_entitlement(self, leave_type):
        """
        :param leave_type: hr.holidays.status record set
        """
        self.ensure_one()

        entitlement = self.holidays_entitlement_ids.filtered(
            lambda e: e.leave_id == leave_type)

        if not entitlement:
            company = self.employee_id.company_id
            entitlement = company.holidays_entitlement_ids.filtered(
                lambda e: e.leave_id == leave_type)

        return entitlement[0] if entitlement else False
