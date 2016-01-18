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

from openerp.tests import common
from openerp.osv import orm


class TestSequentialNumbers(common.TransactionCase):
    """Test sequential numbers with an example from Revenu Québec.
    The sequential numbers are 719970123, 719970134 and 719970145.
    """
    def setUp(self):
        super(TestSequentialNumbers, self).setUp()
        self.user_model = self.registry("res.users")
        self.company_model = self.registry("res.company")
        self.employee_model = self.registry("hr.employee")
        self.slip_model = self.registry("hr.releve_1")
        self.partner_model = self.registry("res.partner")
        self.context = self.user_model.context_get(self.cr, self.uid)
        cr, uid, context = self.cr, self.uid, self.context

        self.country_id = self.registry("res.country").search(
            cr, uid, [('code', '=', 'CA')], context=context)[0]
        self.state_id = self.registry("res.country.state").search(
            cr, uid, [
                ('code', '=', 'QC'), ('country_id', '=', self.country_id)
            ], context=context)[0]

        self.company_ids = [
            self.company_model.create(cr, uid, {
                'name': record[0],
                'rq_first_slip_number': 71997012,
                'rq_last_slip_number': 71997014,
                'street': 'test',
                'street2': 'test',
                'city': 'Québec',
                'zip': 'P1P1P1',
                'country_id': self.country_id,
                'state_id': self.state_id,
            }, context=context)
            for record in [
                ('Company 1',),
                ('Company 2',)
            ]
        ]

        self.address_home_id = self.partner_model.create(
            cr, uid, {
                'name': 'test',
                'street': 'test',
                'street2': 'test',
                'city': 'Québec',
                'zip': 'P1P1P1',
                'country_id': self.country_id,
                'state_id': self.state_id,
            }, context=context)

        self.employee_id = self.employee_model.create(
            cr, uid, {
                'firstname': 'Test',
                'lastname': 'Employee 1',
                'company_id': self.company_ids[0],
                'address_home_id': self.address_home_id,
                'address_id': self.address_home_id,
                'sin': 684242680,
            }, context=context)

        self.employee_2_id = self.employee_model.create(
            cr, uid, {
                'firstname': 'Test',
                'lastname': 'Employee 2',
                'company_id': self.company_ids[0],
                'address_home_id': self.address_home_id,
                'address_id': self.address_home_id,
                'sin': 684242680,
            }, context=context)

        self.employee_3_id = self.employee_model.create(
            cr, uid, {
                'firstname': 'Test',
                'lastname': 'Employee 3',
                'company_id': self.company_ids[0],
                'address_home_id': self.address_home_id,
                'address_id': self.address_home_id,
                'sin': 684242680,
            }, context=context)

    def test_get_next_rq_sequential_number(self):
        cr, uid, context = self.cr, self.uid, self.context

        slip_ids = {
            slip[0]: self.slip_model.create(
                cr, uid, {
                    'employee_id': slip[1],
                    'company_id': slip[2],
                    'slip_type': 'R',
                    'year': slip[3],
                }, context=context)
            for slip in [
                (0, self.employee_id, self.company_ids[0], 2014),
                (1, self.employee_id, self.company_ids[0], 2014),
                (2, self.employee_2_id, self.company_ids[0], 2014),
                (3, self.employee_2_id, self.company_ids[0], 2014),
                (4, self.employee_id, self.company_ids[1], 2014),
                (5, self.employee_id, self.company_ids[0], 2015),
            ]
        }

        slips = {
            index: self.slip_model.browse(
                cr, uid, slip_ids[index], context=context)
            for index in slip_ids
        }

        self.slip_model.compute_amounts(
            cr, uid, [slip_ids[0]], context=context)

        slips[0].refresh()
        self.assertEqual(slips[0].number, 719970123)

        self.slip_model.compute_amounts(
            cr, uid, [slip_ids[1]], context=context)

        slips[1].refresh()
        self.assertEqual(slips[1].number, 719970134)

        self.slip_model.compute_amounts(
            cr, uid, [slip_ids[2]], context=context)

        slips[2].refresh()
        self.assertEqual(slips[2].number, 719970145)

        # All sequential numbers have already been used
        # When we try to assign a new number, it raises
        # an exception
        self.assertRaises(
            orm.except_orm, self.slip_model.compute_amounts,
            cr, uid, [slip_ids[3]], context=context)

        # The slip #4 is for another company, so the
        # sequence restart from the first number
        self.slip_model.compute_amounts(
            cr, uid, [slip_ids[4]], context=context)

        slips[4].refresh()
        self.assertEqual(slips[4].number, 719970123)

        # The slip #5 is in another year, so the
        # sequence restart from the first number
        self.slip_model.compute_amounts(
            cr, uid, [slip_ids[5]], context=context)

        slips[5].refresh()
        self.assertEqual(slips[5].number, 719970123)
