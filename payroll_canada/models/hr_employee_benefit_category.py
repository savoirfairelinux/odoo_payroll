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

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class HrEmployeeBenefitCategory(models.Model):
    _inherit = 'hr.employee.benefit.category'

    is_rpp_dpsp = fields.Boolean(
        'Is RPP or DPSP',
        help="Whether the benefit is a Registered Pension Plan "
        "or a Deferred Profit Sharing Plan",
    )

    @api.one
    @api.constrains('is_rpp_dpsp', 'reference')
    def _check_rpp_dpsp_number(self):
        """
        Check rpp/dpsp registration numbers
        """
        if self.is_rpp_dpsp:
            ref = self.reference
            if (
                not ref or
                len(ref) != 7 or
                not ref.isnumeric()
            ):
                raise ValidationError(_(
                    "RPP and DPSP benefits must have a valid registration "
                    "number. In the field Reference, please enter the "
                    "7 digit number.",
                ))
