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


class HrFiscalSlipBoxBenefitLine(models.Model):
    """Fiscal Slip Box Benefit Line"""

    _name = 'hr.fiscal_slip.box.benefit.line'
    _decription = _(__doc__)

    box_id = fields.Many2one(
        'hr.fiscal_slip.box',
        'Box',
        required=True,
        ondelete='cascade',
    )
    category_id = fields.Many2one(
        'hr.employee.benefit.category',
        'Benefit',
        required=True,
    )
    include_employer = fields.Boolean(
        'Include Employer Contribution',
        default=True,
    )
    include_employee = fields.Boolean(
        'Include Employee Contribution',
        default=True,
    )
    date_from = fields.Date(
        'Date From',
        required=True,
        default=lambda self: fields.Date.today(),
    )
    date_to = fields.Date(
        'Date To',
    )
