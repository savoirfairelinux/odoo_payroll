# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
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

from datetime import datetime

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class HrFiscalSlipBoxBenefitLine(orm.Model):
    _name = 'hr.fiscal_slip.box.benefit.line'
    _decription = 'Fiscal Slip Box Benefit Line'

    _columns = {
        'box_id': fields.many2one(
            'hr.fiscal_slip.box',
            'Box',
            required=True,
            ondelete='cascade',
        ),
        'category_id': fields.many2one(
            'hr.employee.benefit.category',
            'Benefit',
            required=True,
        ),
        'include_employer': fields.boolean(
            'Include Employer Contribution',
        ),
        'include_employee': fields.boolean(
            'Include Employee Contribution',
        ),
        'date_from': fields.date(
            'Date From', required=True,
        ),
        'date_to': fields.date(
            'Date To',
        ),
    }

    _defaults = {
        'include_employer': True,
        'include_employee': True,
        'date_from': lambda self, cr, uid, c={}:
        datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
    }
