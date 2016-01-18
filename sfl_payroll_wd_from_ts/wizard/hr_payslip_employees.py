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

from openerp import api, fields, models


class HrPayslipEmployees(models.TransientModel):

    _inherit = 'hr.payslip.employees'

    import_from_timesheet = fields.Boolean(
        'Import Worked Days From Timesheet',
        default=True,
    )

    @api.multi
    def action_before_computing_sheets(self):
        self.ensure_one()
        res = super(HrPayslipEmployees, self).action_before_computing_sheets()

        if self.import_from_timesheet:
            self.import_timesheets()

        return res

    @api.multi
    def import_timesheets(self):
        self.payslip_ids.import_worked_days()
