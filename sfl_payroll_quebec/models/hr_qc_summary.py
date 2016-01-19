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

from openerp import api, fields, models, _


@api.model
def get_type_codes(self):
    return [
        ('R', _('Original')),
        ('A', _('Amended')),
        ('D', _('Cancelled')),
    ]


class HrQcSummary(models.AbstractModel):
    """Revenu Quebec Fiscal Slip Summary"""

    _name = 'hr.qc.summary'
    _description = _(__doc__)

    state = fields.Selection(
        [
            ('cancelled', 'Cancelled'),
            ('draft', 'Draft'),
            ('sent', 'Sent'),
        ],
        'Status',
        select=True,
        readonly=True,
        default='draft',
    )
    year = fields.Char(
        'Fiscal Year', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda *a: int(fields.Date.today()[0:4]) - 1,
    )
    slip_type = fields.Selection(
        get_type_codes,
        'Type', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default='R',
    )
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user.company_id.id,
    )
    date = fields.Date(
        'Date',
        help='The date of submission to Revenu Quebec.',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=fields.Date.today,
    )
