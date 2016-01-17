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


class HrCRAT4Box(models.Model):
    """CRA T4 Box"""

    _name = 'hr.cra.t4.box'
    _inherits = {'hr.fiscal_slip.box': 'fiscal_slip_box_id'}
    _description = _(__doc__)

    fiscal_slip_box_id = fields.Many2one(
        'hr.fiscal_slip.box',
        'Fiscal Slip Box',
        required=True,
        ondelete='cascade',
    )

    @api.multi
    def compute_amount(self, payslip_ids):
        self.ensure_one()
        return self.fiscal_slip_box_id.compute_amount(payslip_ids)
