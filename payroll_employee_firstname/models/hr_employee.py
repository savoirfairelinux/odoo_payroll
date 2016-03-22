# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    This module copyright (C) 2016 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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

from openerp import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def split_name(self, name):
        if not name:
            return ''
        name_parts = name.split()
        return name_parts[0], ' '.join(name_parts[1:])

    @api.model
    def _update_employee_names(self):
        employees = self.search([
            ('firstname', '=', ' '), ('lastname', '=', ' ')])

        for ee in employees:
            lastname, firstname = self.split_name(ee.name)
            ee.write({
                'firstname': firstname,
                'lastname': lastname,
            })

    @api.multi
    def update_partner_firstname(self):
        for employee in self:
            partners = (
                employee.user_id.partner_id +
                employee.address_home_id
            )

            partners.write({
                'name': employee.firstname,
            })

    @api.model
    def _get_name(self, lastname, firstname):
        name_parts = ' '.join([firstname, lastname]).split()
        return ' '.join(name_parts)

    def _firstname_default(self):
        return ' ' if self.env.context.get('module') else False

    firstname = fields.Char(
        "Firstname", default=_firstname_default)
    lastname = fields.Char(
        "Lastname", required=True, default=_firstname_default)

    @api.model
    def create(self, vals):
        if vals.get('firstname') and vals.get('lastname'):
            vals['name'] = self._get_name(vals['lastname'], vals['firstname'])

        elif vals.get('name'):
            firstname, lastname = self.split_name(vals['name'])
            vals['firstname'] = firstname
            vals['lastname'] = lastname

        return super(HrEmployee, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('firstname') or vals.get('lastname'):
            lastname = vals.get('lastname') or self.lastname or ' '
            firstname = vals.get('firstname') or self.firstname or ' '
            vals['name'] = self._get_name(lastname, firstname)

        elif vals.get('name'):
            firstname, lastname = self.split_name(vals['name'])
            vals['firstname'] = firstname
            vals['lastname'] = lastname

        return super(HrEmployee, self).write(vals)
