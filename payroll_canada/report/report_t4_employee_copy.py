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


def display_address_no_blank_line(partner, name):
    """
    Return a string containing the address with no blank lines
    """
    address = name and '%s\n' % name or ''

    if partner.street:
        address += '%s\n' % partner.street

    if partner.street2:
        address += '%s\n' % partner.street2

    if partner.city:
        address += '%s' % partner.city
        if partner.state_id or partner.zip:
            address += ', '

    if partner.state_id:
        address += '%s ' % partner.state_id.code

    if partner.zip:
        address += '%s' % partner.zip

    if partner.city or partner.state_id or partner.zip:
        address += '\n'

    if partner.country_id:
        address += '%s' % partner.country_id.name

    return address


def get_amount_decimals(amount):
    """
    Return the decimals of the given amount
    example: 1057.42 > 42
    """
    if amount is False:
        return ''
    if amount < 0.01:
        return '.00'
    return '.' + str(int(amount * 100))[-2:]


def get_amount_units(amount):
    """
    Return the units of the given amount
    example: 1057.92 > 1057
    """
    return str(int(amount)) if amount is not False else ''


class report_t4_employee_copy(report_sxw.rml_parse):
    """
    This report is a T4 slip for the employee.
    It is not a copy to be sent to the CRA.
    """
    def __init__(self, cr, uid, name, context):
        super(report_t4_employee_copy, self).__init__(cr, uid, name, context)

        self.localcontext.update({
            'display_address_no_blank_line': display_address_no_blank_line,
            'get_amount_decimals': get_amount_decimals,
            'get_amount_units': get_amount_units,
        })

report_sxw.report_sxw(
    'report.t4_employee_copy',
    'hr.cra.t4',
    'payroll_canada/report/report_t4_employee_copy.rml',
    parser=report_t4_employee_copy,
    header=False
)
