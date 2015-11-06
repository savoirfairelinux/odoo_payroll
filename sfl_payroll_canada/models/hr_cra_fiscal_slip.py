# -*- coding:utf-8 -*-char(

##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
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

from openerp.osv import orm, fields
from openerp.tools.translate import _


def get_province_codes(self, cr, uid, context=None):
    return [
        ('AB', _('Alberta')),
        ('BC', _('British Columbia')),
        ('MB', _('Manitoba')),
        ('NB', _('New Brunswick')),
        ('NL', _('Newfoundland and Labrador')),
        ('NS', _('Nova Scotia')),
        ('NT', _('Northwest Territories')),
        ('NU', _('Nunavut')),
        ('ON', _('Ontario')),
        ('PE', _('Prince Edward Island')),
        ('QC', _('Quebec')),
        ('SK', _('Saskatchewan')),
        ('YT', _('Yukon Territories')),
        ('US', _('United States')),
        ('ZZ', _('Other')),
    ]


def get_type_codes(self, cr, uid, context=None):
    return [
        ('O', _('Original')),
        ('A', _('Amended')),
        ('C', _('Cancelled')),
    ]


class HrCraFiscalSlip(orm.AbstractModel):
    """
    This class is a base for Canada Federal fiscal slips
    """
    _name = 'hr.cra.fiscal_slip'
    _inherit = 'hr.fiscal_slip'
    _description = 'CRA Fiscal Slip'
    _columns = {
        'empt_prov_cd': fields.selection(
            get_province_codes,
            string='Province of employment',
            required=True, type="char",
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'type': fields.selection(
            get_type_codes, 'Type',
            required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
    }

    _defaults = {
        'type': 'O',
    }
