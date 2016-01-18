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

from openerp import api, models, _
from openerp.exceptions import ValidationError


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    @api.multi
    @api.returns('hr.holidays.public.line')
    def get_public_holidays(self):
        """
        Return a list of public holidays for the payslip's period
        """
        self.ensure_one()
        if not self.employee_id.address_id:
            raise ValidationError(_(
                'Insuffisant configuration. You must set the working address '
                'for employee %s') % self.employee_id.name)

        return self.env['hr.holidays.public'].get_holidays_lines(
            self.date_from, self.date_to,
            self.employee_id.address_id.id)
