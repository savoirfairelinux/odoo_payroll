# -*- coding:utf-8 -*-
##############################################################################
#
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

from openerp.tests import common


class TestHrPublicHolidays(common.TransactionCase):

    def setUp(self):
        super(TestHrPublicHolidays, self).setUp()

        self.partner_model = self.env['res.partner']
        self.country_model = self.env['res.country']
        self.state_model = self.env['res.country.state']
        self.employee_model = self.env['hr.employee']
        self.holidays_model = self.env['hr.holidays.public']
        self.line_model = self.env['hr.holidays.public.line']

        self.holidays_model.search(
            [('country_id.code', 'in', ['CA', 'USD'])]).unlink()

        self.country_1 = self.country_model.search([
            ('code', '=', 'CA'),
        ])

        self.country_1.ensure_one()

        self.state_1_1 = self.state_model.create({
            'name': 'Province in Canada 1',
            'code': 'S1_1',
            'country_id': self.country_1.id,
        })

        self.state_1_2 = self.state_model.create({
            'name': 'Province in Canada 2',
            'code': 'S1_2',
            'country_id': self.country_1.id,
        })

        self.country_2 = self.country_model.search([
            ('code', '=', 'US'),
        ])

        self.country_2.ensure_one()

        self.state_2_1 = self.state_model.create({
            'name': 'State in USA 1',
            'code': 'S2_1',
            'country_id': self.country_2.id,
        })

        self.address = self.partner_model.create({
            'name': "John's Adress",
            'country_id': self.country_1.id,
            'state_id': self.state_1_1.id,
        })

        self.employee = self.employee_model.create({
            'name': 'John',
            'address_id': self.address.id,
        })

        self.holidays_1 = self.holidays_model.create({
            'country_id': self.country_1.id,
            'year': 2015,
        })

        self.line_1_1 = self.line_model.create({
            'name': 'Christmas',
            'holidays_id': self.holidays_1.id,
            'date': '2015-12-25',
            'state_ids': [(6, 0, [
                self.state_1_1.id,
            ])],
        })

        self.line_1_2 = self.line_model.create({
            'name': 'Christmas',
            'holidays_id': self.holidays_1.id,
            'date': '2015-12-25',
            'state_ids': [(6, 0, [
                self.state_1_2.id,
            ])],
        })

        self.line_1_3 = self.line_model.create({
            'name': 'Christmas',
            'holidays_id': self.holidays_1.id,
            'date': '2015-12-25',
            'state_ids': [(6, 0, [
                self.state_1_1.id,
                self.state_1_2.id,
            ])],
        })

        self.holidays_2 = self.holidays_model.create({
            'country_id': self.country_1.id,
            'year': 2016,
        })

        self.line_2_1 = self.line_model.create({
            'name': 'New Year',
            'holidays_id': self.holidays_2.id,
            'date': '2016-01-01',
            'state_ids': [],
        })

        self.line_2_2 = self.line_model.create({
            'name': 'Christmas',
            'holidays_id': self.holidays_2.id,
            'date': '2016-12-25',
            'state_ids': [],
        })

        self.holidays_3 = self.holidays_model.create({
            'country_id': self.country_2.id,
            'year': 2015,
        })

        self.line_3_1 = self.line_model.create({
            'name': 'Christmas',
            'holidays_id': self.holidays_3.id,
            'date': '2015-12-25',
            'state_ids': [(6, 0, [
                self.state_2_1.id,
            ])],
        })

        self.line_3_2 = self.line_model.create({
            'name': 'Christmas',
            'holidays_id': self.holidays_3.id,
            'date': '2015-12-25',
            'state_ids': [],
        })

    def test_get_holidays_lines(self):
        res = self.holidays_model.get_holidays_lines(
            '2015-12-15', '2016-01-01', self.address.id)

        expected_res = (
            self.line_1_1 + self.line_1_3 +
            self.line_2_1
        )

        self.assertEqual(res, expected_res)

    def test_get_holidays_lines_no_state(self):
        self.address.write({'state_id': False})

        res = self.holidays_model.get_holidays_lines(
            '2015-12-15', '2016-01-01', self.address.id)

        self.assertEqual(res, self.line_2_1)

    def test_get_holidays_lines_date_before(self):
        res = self.holidays_model.get_holidays_lines(
            '2015-12-15', '2015-12-31', self.address.id)

        expected_res = self.line_1_1 + self.line_1_3

        self.assertEqual(res, expected_res)

    def test_get_holidays_lines_date_after(self):
        res = self.holidays_model.get_holidays_lines(
            '2015-12-26', '2016-01-01', self.address.id)

        self.assertEqual(res, self.line_2_1)
