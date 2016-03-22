# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 - 2016 Savoir-faire Linux. All Rights Reserved.
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
    'name': 'Quebec - Payroll',
    'category': 'Localization',
    'version': '1.0',
    'license': 'AGPL-3',
    'description': """
Quebec Payroll Rules
====================
 * Add all Quebec Salary Rules
 * Add the Releve 1 and the Summary 1

Contributors
------------
* Jonatan Cloutier <jonatan.cloutier@savoirfairelinux.com>
* Maxime Chambreuil <maxime.chambreuil@savoirfairelinux.com>
* Mathieu Benoit <mathieu.benoit@savoirfairelinux.com>
* Sandy Carter <sandy.carter@savoirfairelinux.com>
* Pierre Lamarche <pierre.lamarche@savoirfairelinux.com>
* David Dufresne <david.dufresne@savoirfairelinux.com>
""",
    'author': "Savoir-faire Linux,Odoo Community Association (OCA)",
    'website': 'http://www.savoirfairelinux.com',
    'depends': [
        'payroll_canada',
    ],
    'data': [
        'data/hr_contribution_register.xml',
        'data/hr_income_tax_exemption.xml',
        'data/salary_rules/cpp.xml',
        'data/salary_rules/ei.xml',
        'data/salary_rules/fit.xml',
        'data/salary_rules/qit.xml',
        'data/salary_rules/qpip.xml',
        'data/salary_rules/qpp.xml',
        'data/salary_rules/hsf.xml',
        'data/salary_rules/csst.xml',
        'data/salary_rules/cnt.xml',
        'data/salary_rules/wsdrf.xml',
        'data/hr_deduction_jurisdiction.xml',
        'data/hr_deduction_category.xml',
        'data/public_holidays/2016.xml',
        'data/hr_holidays_entitlement.xml',
        'data/hr_structure.xml',
        'data/hr_cra_t4_box.xml',
        'data/hr_releve_1_box.xml',
        'data/hr_releve_1_other_amount.xml',
        'data/hr_releve_1_summary_box.xml',
        'data/salary_rule_variables/2014.xml',
        'data/salary_rule_variables/2015.xml',
        'data/salary_rule_variables/2016.xml',
        'views/res_company.xml',
        'views/hr_employee.xml',
        'views/hr_releve_1.xml',
        'views/hr_releve_1_box.xml',
        'views/hr_releve_1_summary.xml',
        'report/hr_releve_1_report.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'external_dependencies': {
        'python': ['elaphe'],
    },
    'demo': ['demo/demo_data.xml'],
    'test': [],
    'installable': True,
}
