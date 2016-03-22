# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2015 Savoir-faire Linux
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
{
    'name': 'Payroll Accounting',
    'version': '1.0.0',
    'category': 'Human Resources',
    'author': 'OpenERP SA,Savoir-faire Linux',
    'website': 'https://www.odoo.com/page/employees',
    'depends': [
        'payroll_base',
        'account',
        'hr_expense',
    ],
    'data': [
        'views/hr_payslip.xml',
        'views/hr_payslip_run.xml',
        'views/hr_salary_rule.xml',
        'views/res_company.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
