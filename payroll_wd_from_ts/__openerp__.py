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

{
    'name': 'Worked Days From Timesheet',
    'version': '1.0.0',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'author': "Savoir-faire Linux",
    'website': 'https://www.savoirfairelinux.com',
    'depends': [
        'payroll_base',
        'hr_timesheet_sheet',
    ],
    'data': [
        'views/hr_payslip.xml',
        'wizard/hr_payslip_employees.xml',
    ],
    'installable': True,
}
