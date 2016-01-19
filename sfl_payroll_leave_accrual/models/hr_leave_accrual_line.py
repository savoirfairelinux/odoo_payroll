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


class HrLeaveAccrualLine(models.AbstractModel):
    """Leave Accrual Line"""

    _name = 'hr.leave.accrual.line'
    _description = _(__doc__)

    name = fields.Char(
        'Name',
        required=True,
    )
    source = fields.Selection(
        [
            ('payslip', 'Payslip Line'),
            ('allocation', 'Allocation'),
            ('manual', 'Entered Manually'),
        ],
        type='char',
        string="Source",
        required=True,
        default='manual',
    )
    date = fields.Date(
        'Date',
        required=True,
        default=fields.Date.today,
    )

    _order = 'date desc'
