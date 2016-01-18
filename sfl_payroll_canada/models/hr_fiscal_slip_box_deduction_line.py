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


class HrFiscalSlipBoxDeductionLine(models.Model):
    """Fiscal Slip Box Deduction Line"""

    _name = 'hr.fiscal_slip.box.deduction.line'
    _decription = _(__doc__)

    box_id = fields.Many2one(
        'hr.fiscal_slip.box',
        'Box',
        required=True,
        ondelete='cascade',
    )
    category_id = fields.Many2one(
        'hr.deduction.category',
        'Deduction',
        required=True,
    )
    date_from = fields.Date(
        'Date From', required=True,
        default=lambda self: fields.Date.today(),
    )
    date_to = fields.Date(
        'Date To',
    )

    _order = 'date_to desc,date_from desc'
