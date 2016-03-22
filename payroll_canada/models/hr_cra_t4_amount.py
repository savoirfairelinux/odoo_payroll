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

from openerp import fields, models, _
import openerp.addons.decimal_precision as dp


class HrCRAT4Amount(models.Model):
    """CRA T4 Amount"""

    _name = 'hr.cra.t4.amount'
    _description = _(__doc__)

    slip_id = fields.Many2one(
        'hr.cra.t4',
        'T4 Slip',
        required=True,
        ondelete='cascade',
    )
    box_id = fields.Many2one(
        'hr.cra.t4.box',
        'T4 Box',
        required=True,
        ondelete='restrict',
    )
    amount = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Payroll'),
        required=True,
    )
    is_other_amount = fields.Boolean(
        'Is Other Amount',
        related='box_id.is_other_amount',
        readonly=True,
    )
    code = fields.Char(
        'Code',
        related='box_id.code',
        readonly=True,
    )
    xml_tag = fields.Char(
        'XML Tag',
        related='box_id.xml_tag',
        readonly=True,
    )

    _order = 'box_id'
