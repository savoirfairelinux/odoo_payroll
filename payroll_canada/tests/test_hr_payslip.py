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

from datetime import datetime

from openerp.tests import common


class TestPayslipBase(common.TransactionCase):
    def ref(self, ext_id):
        if '.' in ext_id:
            module, ext_id = ext_id.split('.')
        else:
            module = 'payroll_canada'

        return self.data_model.get_object_reference(
            self.cr, self.uid, module, ext_id)[1]

    def setUp(self):
        super(TestPayslipBase, self).setUp()
        self.data_model = self.registry('ir.model.data')
        self.partner_model = self.registry('res.partner')
        self.country_model = self.registry("res.country")
        self.company_model = self.registry('res.company')
        self.employee_model = self.registry('hr.employee')
        self.user_model = self.registry("res.users")
        self.payslip_model = self.registry("hr.payslip")
        self.worked_days_model = self.registry("hr.payslip.worked_days")
        self.contract_model = self.registry("hr.contract")
        self.job_model = self.registry("hr.job")
        self.activity_model = self.registry("hr.activity")
        self.rate_class_model = self.registry("hr.hourly.rate.class")
        self.input_model = self.registry("hr.payslip.input")
        self.module_model = self.registry('ir.module.module')
        self.input_category_model = self.registry('hr.payslip.input.category')
        self.rule_model = self.registry('hr.salary.rule')
        self.context = self.user_model.context_get(self.cr, self.uid)

        cr, uid, context = self.cr, self.uid, self.context

        self.canada_id = self.registry("res.country").search(
            cr, uid, [('code', '=', 'CA')], context=context
        )[0]

        self.state_id = self.registry("res.country.state").search(
            cr, uid, [
                ('code', '=', 'AB'), ('country_id', '=', self.canada_id)
            ], context=context)[0]

        self.jurisdiction_id = self.data_model.get_object_reference(
            cr, uid, 'payroll_canada', 'jurisdiction_federal')[1]

        # Create a company
        self.company_id = self.company_model.create(cr, uid, {
            'name': 'Company 1',
            'currency_id': self.env.ref('base.CAD').id,
            'street': 'test',
            'street2': 'test',
            'city': 'Regina',
            'zip': 'P1P1P1',
            'country_id': self.canada_id,
            'state_id': self.state_id,
            'week_start': '3',
            'cra_transmitter_number': 'MM000000',
            'cra_payroll_number': '123456789RP1234',
            'holidays_entitlement_ids': [
                (4, self.ref('standard_vacation_entitlement'))],
        }, context=context)

        # Create an address
        self.address_id = self.partner_model.create(cr, uid, {
            'name': 'test',
            'street': 'test',
            'street2': 'test',
            'city': 'Regina',
            'zip': 'P1P1P1',
            'country_id': self.canada_id,
            'state_id': self.state_id,
        }, context=context)

        # Create an employee
        self.employee_id = self.employee_model.create(cr, uid, {
            'firstname': 'John',
            'lastname': 'Doe',
            'company_id': self.company_id,
            'address_id': self.address_id,
            'address_home_id': self.address_id,
            'sin': 901208505,
        }, context=context)

        # Create jobs for the employee
        self.job_id = self.job_model.create(
            cr, uid, {'name': 'Job 1'}, context=context)

        self.job_2_id = self.job_model.create(
            cr, uid, {'name': 'Job 2'}, context=context)

        # Create 2 hourly rate classes
        self.rate_class_id = self.rate_class_model.create(
            cr, uid, {
                'name': 'Test',
                'line_ids': [
                    (0, 0, {
                        'date_start': '2014-01-01',
                        'rate': 30,
                    }),
                ],
            }, context=context)

        self.rate_class_2_id = self.rate_class_model.create(cr, uid, {
            'name': 'Test',
            'line_ids': [
                (0, 0, {
                    'date_start': '2014-01-01',
                    'rate': 40,
                }),
            ],
        }, context=context)

        # Create a contract
        self.contract_id = self.contract_model.create(cr, uid, {
            'employee_id': self.employee_id,
            'name': 'Contract 1',
            'wage': 52000,
            'schedule_pay': 'weekly',
            'worked_hours_per_pay_period': 40,
            'weeks_of_vacation': 4,
            'salary_computation_method': 'hourly',
            'holidays_entitlement_ids': [(4, self.ref(
                'standard_vacation_entitlement'))],
            'contract_job_ids': [
                (0, 0, {
                    'job_id': self.job_id,
                    'is_main_job': False,
                    'hourly_rate_class_id': self.rate_class_id,
                }),
                (0, 0, {
                    'job_id': self.job_2_id,
                    'is_main_job': True,
                    'hourly_rate_class_id': self.rate_class_2_id,
                }),
            ],
        }, context=context)

        # Get the id of the activity for job 1 and job 2
        self.job_activity_id = self.job_model.browse(
            cr, uid, self.job_id, context=context).activity_ids[0].id

        self.job_2_activity_id = self.job_model.browse(
            cr, uid, self.job_2_id, context=context).activity_ids[0].id

        self.vac_activity_id = self.ref(
            'payroll_activity.activity_holiday_status_vacation')

        self.comp_activity_id = self.ref(
            'payroll_activity.activity_holiday_status_comp')

        self.public_activity_id = self.ref(
            'payroll_activity.activity_holiday_status_public')

        self.sl_activity_id = self.ref(
            'payroll_activity.activity_holiday_status_sl')

        self.unpaid_activity_id = self.ref(
            'payroll_canada.activity_holiday_status_vac_unpaid')

        self.account_module_id = self.module_model.search(cr, uid, [
            ('latest_version', '!=', False),
            ('name', '=', 'hr_payroll_account'),
        ], context=context)

        if self.account_module_id:
            self.setup_payroll_accounting()

    def create_fiscal_year(self, year, company_id=False):
        cr, uid, context = self.cr, self.uid, self.context

        fy_id = self.fiscal_year_model.create(cr, uid, {
            'name': 'Test %s' % year,
            'code': 'FY%s' % year,
            'company_id': company_id or self.company_id,
            'date_start': datetime(year, 1, 1),
            'date_stop': datetime(year, 12, 31),
        }, context=context)

        fy = self.fiscal_year_model.browse(cr, uid, fy_id, context=context)
        fy.create_period()

    def setup_payroll_accounting(self):
        self.move_model = self.registry('account.move')
        self.account_model = self.registry('account.account')
        self.journal_model = self.registry('account.journal')
        self.fiscal_year_model = self.registry('account.fiscalyear')
        cr, uid, context = self.cr, self.uid, self.context

        self.create_fiscal_year(2013)
        self.create_fiscal_year(2014)
        self.create_fiscal_year(2015)

        self.expense_type = self.ref('account.data_account_type_expense')
        self.payable_type = self.ref('account.data_account_type_payable')

        self.journal_id = self.journal_model.create(cr, uid, {
            'company_id': self.company_id,
            'name': 'Payroll Journal',
            'code': 'PAYJ',
            'type': 'general',
        }, context=context)

    def create_payslip(self, vals):
        """ If module hr_payroll_account is installed, we need to set the journal_id
        field """
        if self.account_module_id:
            vals['journal_id'] = self.journal_id

        return self.payslip_model.create(
            self.cr, self.uid, vals, context=self.context)


class TestHrPayslip(TestPayslipBase):

    def setUp(self):
        super(TestHrPayslip, self).setUp()

        cr, uid, context = self.cr, self.uid, self.context
        # Create a payslip
        self.payslip_id = self.create_payslip({
            'company_id': self.company_id,
            'employee_id': self.employee_id,
            'contract_id': self.contract_id,
            'date_from': '2014-11-17',
            'date_to': '2014-11-30',
            'date_payment': '2014-11-30',
        })

        for line in [
            # date, nb_hours, activity_id, hourly_rate, rate (%)
            ('2014-11-17', 11, self.job_activity_id, 15, 90),
            ('2014-11-18', 13, self.vac_activity_id, 10, 110),
            ('2014-11-30', 23, self.comp_activity_id, 13, 150),
        ]:
            self.worked_days_model.create(
                cr, uid, {
                    'date': line[0],
                    'number_of_hours': line[1],
                    'activity_id': line[2],
                    'hourly_rate': line[3],
                    'rate': line[4],
                    'payslip_id': self.payslip_id,
                }, context=context)

    def test_get_pays_since_beginning(self):
        """
        Test the get_pays_since_beginning method for different values
        of pays_per_year on contract
        """
        cr, uid, context = self.cr, self.uid, self.context

        payslip = self.payslip_model.browse(
            cr, uid, self.payslip_id, context=context)

        for case in [
            # (pays_per_year, res)
            (52, 47),
            (26, 24),
            (24, 22),
            (13, 12),
            (6, 6),
        ]:
            res = payslip.get_pays_since_beginning(case[0])

            self.assertEqual(res, case[1])

    def test_sum_payslip_input(self):
        cr, uid, context = self.cr, self.uid, self.context
        payslip = self.payslip_model.browse(
            cr, uid, self.payslip_id, context=context)

        bonus_id = self.ref('payslip_input_bonus')
        retro_pay_id = self.ref('payslip_input_retro_pay')

        for input_line in [
            (bonus_id, 370),
            (retro_pay_id, 400),
            (bonus_id, 300),
            (bonus_id, 330),
            (retro_pay_id, 400),
        ]:
            self.input_model.create(
                cr, uid, {
                    'name': 'Test',
                    'category_id': input_line[0],
                    'amount': input_line[1],
                    'payslip_id': self.payslip_id,
                }, context=context)

        rule_id = self.ref('rule_ca_bonus')
        rule = self.rule_model.browse(cr, uid, rule_id, context=context)

        res = rule.sum_payslip_input(payslip)
        self.assertEqual(res, 1000)

        rule.reduce_payslip_input_amount(payslip, 800)

        res = rule.sum_payslip_input(payslip)
        self.assertEqual(res, 200)

        rule.reduce_payslip_input_amount(payslip, 800)

        res = rule.sum_payslip_input(payslip)
        self.assertEqual(res, 0)

        payslip.refresh()

        for line in payslip.input_line_ids:
            self.assertGreaterEqual(line.amount, 0)
