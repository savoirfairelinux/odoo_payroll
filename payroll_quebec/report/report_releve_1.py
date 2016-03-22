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

from openerp.report import report_sxw
from openerp.addons.payroll_canada.report.report_t4_employee_copy import (
    display_address_no_blank_line, get_amount_decimals, get_amount_units)


class report_releve_1_copy_1(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_releve_1_copy_1, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'content_qr_bar_code': True,
            'instructions': False,
            'releve_type': '12EE',
            'display_address_no_blank_line': display_address_no_blank_line,
            'get_amount_units': get_amount_units,
            'get_amount_decimals': get_amount_decimals,
        })
        # The barcode is only required for the copy 1
        self.pool['hr.releve_1'].make_dtmx_barcode(
            cr, uid, context['active_ids'], context=context)


report_sxw.report_sxw(
    'report.releve_1_copy_1',
    'hr.releve_1',
    'payroll_quebec/report/report_releve_1.rml',
    parser=report_releve_1_copy_1,
    header=False
)


class report_releve_1_copy_2(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_releve_1_copy_2, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'content_qr_bar_code': False,
            'instructions': True,
            'releve_type': '12EF',
            'display_address_no_blank_line': display_address_no_blank_line,
            'get_amount_units': get_amount_units,
            'get_amount_decimals': get_amount_decimals,
        })


report_sxw.report_sxw(
    'report.releve_1_copy_2',
    'hr.releve_1',
    'payroll_quebec/report/report_releve_1.rml',
    parser=report_releve_1_copy_2,
    header=False
)
