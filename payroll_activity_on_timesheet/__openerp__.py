# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 - 2015 Savoir-faire Linux. All Rights Reserved.
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

{
    'name': 'Activity on Timesheet',
    'version': '1.0.0',
    'license': 'AGPL-3',
    'category': 'Generic Modules/Human Resources',
    'author': "Savoir-faire Linux,Odoo Community Association (OCA)",
    'website': 'https://www.savoirfairelinux.com/',
    'depends': [
        'payroll_activity',
        'hr_timesheet_sheet',
        'payroll_contract_jobs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_contract_security.xml',
        'views/account_analytic_line.xml',
        'views/hr_timesheet_sheet.xml',
        'views/account_analytic_account.xml',
        'data/account_analytic_account_data.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'images': [],
    #'qweb': ['static/src/xml/timesheet.xml'],
}
