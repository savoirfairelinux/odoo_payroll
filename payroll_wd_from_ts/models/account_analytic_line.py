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

from itertools import groupby

from openerp import _, api, fields, models
from openerp.exceptions import ValidationError


class AccountAnalyticLine(models.Model):

    _inherit = 'account.analytic.line'

    worked_days_id = fields.Many2one(
        'hr.payslip.worked_days',
        'Payslip Worked Days',
    )

    @api.multi
    def export_to_worked_days(self, payslip_id):
        """
        Export a record set of timesheets to the worked days
        of a payslip.

        For each timesheets that map exactly to the same worked days
        field values, only one record is created.
        """
        # if self.filtered(lambda ts: not ts.is_timesheet):
        #     raise ValidationError(_(
        #         'Only timesheets can be exported to worked days'))

        if self.sudo().mapped('worked_days_id'):
            raise ValidationError(_(
                'You are attempting to export a timesheet that was already '
                'exported to a payslip'))

        # Map every single timesheet
        mapped_timesheets = []

        for ts in self:
            worked_days_vals = list(ts.worked_days_mapping().iteritems())
            worked_days_vals.sort()
            mapped_timesheets.append((
                ts.id, ts.unit_amount, worked_days_vals))

        # Group timesheets together
        # If 2 or more timesheets are mapped the same way
        grouped_timesheets = groupby(mapped_timesheets, lambda t: t[2])

        for key, group in grouped_timesheets:
            timesheet_list = list(group)
            timesheet_ids = tuple(t[0] for t in timesheet_list)
            worked_days_vals = dict(key)
            worked_days_vals['payslip_id'] = payslip_id
            worked_days_vals['imported_from_timesheets'] = True
            worked_days_vals['number_of_hours'] = sum(
                t[1] for t in timesheet_list)
            new_worked_days = self.env['hr.payslip.worked_days'].create(
                worked_days_vals)

            # Bind the timesheet to the worked days
            # Bypass the orm because the timesheet can not
            # be modified when it's state is done.
            cr = self.env.cr
            cr.execute(
                """UPDATE account_analytic_line
                SET worked_days_id = %s WHERE id in %s
                """, (new_worked_days.id, timesheet_ids, ))

    @api.multi
    def worked_days_mapping(self):
        """
        Map a single timesheet record to a dict of field values
        that would be used to generate a worked_days record.
        """
        self.ensure_one()
        return {
            'name': _('Imported From Timesheet'),
            'date': self.date,
        }
