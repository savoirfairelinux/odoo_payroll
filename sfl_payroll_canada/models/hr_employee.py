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

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def check_personal_info(self):
        """
        Check the employee's personal data before creating
        a fiscal slip.

        The employee must have a first name, an home address and the
        home address must contain the employee's SIN.
        """
        for employee in self:
            if not employee.firstname:
                raise ValidationError(
                    _("The employee %s's first name is not set.") %
                    employee.name)

            if not employee.sin:
                raise ValidationError(
                    _("The employee %s's social insurance number "
                        "is not set.") % employee.name)

            address = employee.address_home_id

            if not address:
                raise ValidationError(
                    _("The employee %s's home address is not set.") %
                    employee.name)

            for field in [
                ('street', _('Street Line 1')),
                ('country_id', _('Country')),
                ('state_id', _('Province')),
                ('zip', _('Postal Code')),
            ]:
                if not address[field[0]]:
                    raise ValidationError(
                        _("The employee %s's home address is incomplete. "
                            "The field %s is missing.") % (
                            employee.name, field[1]))

            address_work = employee.address_id

            if not address_work:
                raise ValidationError(
                    _("The employee %s's working address is not set.") %
                    employee.name)

            # The working province of the employee is required in the T4
            if not address_work.state_id:
                raise ValidationError(
                    _("The employee %s's working address "
                        "has no province defined.") %
                    employee.name)

            # The working country of the employee is required
            # to compute payslips
            if not address_work.country_id:
                raise ValidationError(
                    _("The employee %s's working address "
                        "has no country defined.") %
                    employee.name)

    employee_number = fields.Char(
        'Employee Number',
    )
    lastname_initial = fields.Char(
        'Last Name initial',
        size=1
    )
    sin = fields.Float(
        'Social Insurance Number',
        digits=(9, 0),
        groups="base.group_hr_manager",
    )

    @api.multi
    def onchange_sin(self, sin):
        ret = {'value': 0}

        def digits_of(n):
            return [int(d) for d in str(n)]

        def luhn_checksum(sin):
            digits = digits_of(sin)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = 0
            checksum += sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10

        def is_luhn_valid(sin):
            return luhn_checksum(sin) == 0

        if is_luhn_valid(sin):
            ret['value'] = sin
        else:
            ret['value'] = 0
            ret['warning'] = {
                'title': 'Error',
                'message': _('The number provided is not a valid SIN number !')
            }
        return ret
