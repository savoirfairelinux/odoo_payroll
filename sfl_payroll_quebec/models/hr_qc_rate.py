# -*- coding:utf-8 -*-#########################################################
#
#    Copyright (C) 2016 Savoir-faire Linux. All Rights Reserved.
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

from openerp import fields, models, _


class HrQcRate(models.Model):
    """Quebec Contribution Rate"""

    _name = 'hr.qc.rate'
    _description = _(__doc__)

    date_from = fields.Date(
        'Date From',
        required=True,
    )
    date_to = fields.Date(
        'Date To',
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
    )
    rate = fields.Float(
        'Rate',
        digits=(2, 2),
        required=True,
        help="Enter 2.5 for a rate of 2.5 %."
    )
    contribution_type = fields.Selection(
        [
            ('csst', 'CSST'),
            ('hsf', 'Health Services Fund'),
        ],
        required=True,
        type='char',
        string='Type',
    )
