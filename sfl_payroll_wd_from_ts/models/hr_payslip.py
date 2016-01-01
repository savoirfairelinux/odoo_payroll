# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux All Rights Reserved.
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

from openerp import api, models, _
from openerp.exceptions import ValidationError


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    @api.one
    def import_worked_days(self, raise_exception=True):
        """
        Retrieve the employee's timesheets for a payslip period
        and create worked days records from the imported timesheets
        """
        employee = self.employee_id

        # Delete old imported worked_days
        # The reason to delete these records is that the user may make
        # corrections to his timesheets and then reimport these.
        old_worked_days = self.worked_days_line_ids.filtered(
            lambda wd: wd.imported_from_timesheets)

        old_worked_days.unlink()

        date_from = self.date_from
        date_to = self.date_to

        sheets = self.env['hr_timesheet_sheet.sheet'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'done'),
            '|',
            '|',
            '&',
            ('date_from', '>=', date_from),
            ('date_from', '<=', date_to),
            '&',
            ('date_to', '>=', date_from),
            ('date_to', '<=', date_to),
            '&',
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
        ])

        if not sheets and raise_exception:
            raise ValidationError(_(
                "There is no approved Timesheets for "
                "the entire Payslip period for employee %s." %
                employee.name
            ))

        timesheets = sheets.mapped('timesheet_ids').filtered(
            lambda t: date_from <= t.date <= date_to)

        timesheets.export_to_worked_days(self.id)
