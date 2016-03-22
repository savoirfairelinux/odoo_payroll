# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Michael Telahun Makonnen
#    Copyright (C) 2015 Savoir-faire Linux
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    'name': 'Public Holidays',
    'version': '1.0.0',
    'category': 'Human Resources',
    'author': "Michael Telahun Makonnen <mmakonnen@gmail.com>,"
              "Savoir-faire Linux",
    'website': 'https://savoirfairelinux.com',
    'license': 'AGPL-3',
    'depends': [
        'payroll_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_public_holidays_view.xml',
    ],
    'installable': True,
}
