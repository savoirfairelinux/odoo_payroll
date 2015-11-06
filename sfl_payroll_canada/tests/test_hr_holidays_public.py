# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
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

from .test_hr_payslip import TestPayslipBase


class TestHrPublicHolidays(TestPayslipBase):
    def setUp(self):
        super(TestHrPublicHolidays, self).setUp()
        self.payslip_model = self.registry("hr.payslip")
        self.public_holidays_model = self.registry("hr.holidays.public")
        self.country_model = self.registry("res.country")
        self.state_model = self.registry("res.country.state")
        self.user_model = self.registry("res.users")
        self.context = self.user_model.context_get(self.cr, self.uid)

        cr, uid, context = self.cr, self.uid, self.context

        canada_id = self.registry("res.country").search(
            self.cr, self.uid, [('code', '=', 'CA')], context=self.context
        )[0]
        usa_id = self.registry("res.country").search(
            self.cr, self.uid, [('code', '=', 'US')], context=self.context
        )[0]

        self.states = {
            state[0]: self.state_model.search(self.cr, self.uid, [
                ('country_id', '=', state[1]), ('code', '=', state[0])
            ], context=self.context)[0]

            for state in [
                ('QC', canada_id),
                ('ON', canada_id),
                ('CA', usa_id),
                ('ME', usa_id),
            ]
        }

        self.holiday_1 = self.public_holidays_model.create(
            self.cr, self.uid, {
                'year': 2014,
                'country_id': canada_id,
                'line_ids': [
                    (0, 0, {
                        'date': '2014-01-02',
                        'name': 'Holiday 1',
                        'state_ids': [
                            (6, 0, [self.states['QC'], self.states['ON']])]
                    }),
                    (0, 0, {
                        'date': '2014-01-15',
                        'name': 'Holiday 2',
                        'state_ids': [(6, 0, [self.states['QC']])]
                    }),
                    (0, 0, {
                        'date': '2014-01-10',
                        'name': 'Holiday 3',
                        'state_ids': [(6, 0, [])]
                    }),
                    (0, 0, {
                        'date': '2014-01-16',
                        'name': 'Test',
                        'state_ids': [
                            (6, 0, [self.states['QC'], self.states['ON']])]
                    }),
                    (0, 0, {
                        'date': '2014-01-01',
                        'name': 'Test',
                        'state_ids': [
                            (6, 0, [self.states['QC'], self.states['ON']])]
                    }),
                    (0, 0, {
                        'date': '2014-01-03',
                        'name': 'Test',
                        'state_ids': [(6, 0, [self.states['ON']])]
                    }),
                ],
            }, context=self.context)

        self.holiday_2 = self.public_holidays_model.create(
            self.cr, self.uid, {
                'year': 2013,
                'country_id': canada_id,
                'line_ids': [(0, 0, {
                    'date': '2013-01-02',
                    'name': 'Test',
                    'state_ids': [(6, 0, [
                        self.states['QC'], self.states['ON']])]
                })]
            }, context=self.context)

        self.holiday_3 = self.public_holidays_model.create(
            self.cr, self.uid, {
                'year': 2014,
                'country_id': usa_id,
                'line_ids': [(0, 0, {
                    'date': '2014-01-02',
                    'name': 'Test',
                    'state_ids': [(6, 0, [
                        self.states['ME'], self.states['CA']])]
                })]
            }, context=self.context)

        # The following leave has no country, so it applies for every country
        self.holiday_4 = self.public_holidays_model.create(
            self.cr, self.uid, {
                'year': 2014,
                'country_id': False,
                'line_ids': [(0, 0, {
                    'date': '2014-01-02',
                    'name': 'Test',
                    'state_ids': False,
                })]
            }, context=self.context)

        self.partner_model.write(cr, uid, [self.address_id], {
            'state_id': self.states['QC'],
        }, context=context)

        self.payslip_id = self.payslip_model.create(cr, uid, {
            'employee_id': self.employee_id,
            'contract_id': self.contract_id,
            'date_from': '2014-01-02',
            'date_to': '2014-01-15',
        }, context=context)

        self.payslip = self.payslip_model.browse(
            cr, uid, self.payslip_id, context=context)

    def test_sum_public_holidays(self):
        """ Test sum_public_holidays with a state given has parameter
        """
        res = self.payslip.get_public_holidays()

        # Holidays 1, 2, 3 and 4 must be found.
        # The date is between 2014-01-02 and 2014-01-15
        # QC is in state_ids or state_ids is False
        self.assertEqual(len(res), 4)
