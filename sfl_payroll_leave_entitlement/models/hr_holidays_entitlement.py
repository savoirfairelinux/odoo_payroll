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


class HrHolidaysEntitlement(models.Model):
    """Holidays Entitlement"""

    _name = 'hr.holidays.entitlement'
    _description = _(__doc__)

    name = fields.Char(
        'Name',
        required=True,
    )
    month_start = fields.Selection(
        [
            ('1', 'January'),
            ('2', 'February'),
            ('3', 'March'),
            ('4', 'April'),
            ('5', 'May'),
            ('6', 'June'),
            ('7', 'July'),
            ('8', 'August'),
            ('9', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),
        ],
        required=True,
        type='char',
        string='Month Start',
        default='1',
    )
    day_start = fields.Integer(
        'Day Start',
        required=True,
        default=1,
    )
    leave_id = fields.Many2one(
        'hr.holidays.status',
        'Leave Type',
        required=True,
    )
