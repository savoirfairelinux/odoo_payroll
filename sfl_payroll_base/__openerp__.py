# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2015 Savoif-faire Linux
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
    'name': 'Advanced Payroll',
    'version': '1.0.0',
    'category': 'Human Resources',
    'author': 'OpenERP SA,Savoir-faire Linux',
    'website': 'https://www.savoirfairelinux.com',
    'depends': [
        'hr',
        'hr_contract',
        'hr_holidays',
        'decimal_precision',
        'report',
    ],
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'wizard/hr_payslip_employees.xml',
        'views/menu.xml',
        'views/hr_contract.xml',
        'views/hr_holidays_status.xml',
        'views/hr_salary_rule.xml',
        'views/hr_salary_rule_category.xml',
        'views/hr_payslip.xml',
        'views/hr_employee.xml',
        'views/hr_payslip_run.xml',
        'views/hr_payroll_structure.xml',
        'views/hr_payslip_line.xml',
        'views/res_company.xml',
        'workflow/hr_payslip.xml',
        'data/hr_payroll_sequence.xml',
        'data/hr_payroll_data.xml',
        'report/hr_payroll_report.xml',
        'report/report_payslip.xml',
        'report/report_payslip_details.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
