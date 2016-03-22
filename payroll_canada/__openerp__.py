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
    'name': 'Canada - Payroll',
    'version': '1.0.0',
    'license': 'AGPL-3',
    'author': "Savoir-faire Linux",
    'website': 'https://savoirfairelinux.com',
    'depends': [
        'document',
        'payroll_hourly_rate',
        'l10n_ca_toponyms',
        'payroll_period',
        'payroll_employee_exemption',
        'payroll_employee_benefit',
        'payroll_benefit_exemption',
        'payroll_benefit_on_job',
        'payroll_benefit_percent',
        'payroll_public_holidays',
        'payroll_amount_ytd',
        'payroll_leave_accrual',
        'payroll_rule_variable',
        'payroll_activity',
        'payroll_tax_deduction',
        'payroll_leave_entitlement',
        'payroll_employee_firstname',
    ],
    'data': [
        'views/menu.xml',
        'views/res_company.xml',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
        'views/hr_cra_t4.xml',
        'views/hr_cra_t4_box.xml',
        'views/hr_cra_t4_summary.xml',
        'views/hr_employee_benefit_category.xml',
        'data/hr_contribution_register.xml',
        'data/hr_holidays_entitlement.xml',
        'data/hr_deduction_jurisdiction.xml',
        'data/hr_income_tax_exemption.xml',
        'data/hr_employee_benefit_category.xml',
        'data/hr_holidays_status.xml',
        'data/salary_rules/base.xml',
        'data/salary_rules/ben.xml',
        'data/salary_rules/ei.xml',
        'data/salary_rules/cpp.xml',
        'data/salary_rules/fit.xml',
        'data/salary_rules/pension_plans.xml',
        'data/salary_rules/vacation.xml',
        'data/salary_rules/public_holidays.xml',
        'data/salary_rules/sick_leaves.xml',
        'data/salary_rules/compensatory.xml',
        'data/hr_deduction_category.xml',
        'data/hr_payslip_input_category.xml',
        'data/hr_cra_t4_box.xml',
        'data/hr_cra_t4_other_amount.xml',
        'data/hr_cra_t4_summary_box.xml',
        'data/hr_structure.xml',
        'data/hr_leave_accrual.xml',
        'data/public_holidays/2016.xml',
        'data/salary_rule_variables/2014.xml',
        'data/salary_rule_variables/2015.xml',
        'data/salary_rule_variables/2016.xml',
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'report/hr_payroll_report.xml',
    ],
    'external_dependencies': {
        'python': ['iso3166'],
    },
    'test': [],
    'demo': ['demo/demo_data.xml'],
    'installable': True,
}
