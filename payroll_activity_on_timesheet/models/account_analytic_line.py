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


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    activity_id = fields.Many2one(
        'hr.activity',
        'Activity',
    )

    @api.onchange('project_id')
    def onchange_project_id(self):

        # If an activity and an account are given, check if the activity
        # is authorized for the account. If the activity is authorized,
        # return the same activity_id.
        if not self.activity_id:
            self.activity_id = False

        elif self.account_id:
            account = self.account_id

            auth_activities = account.authorized_activity_ids
            activity = self.activity_id

            if activity in auth_activities or (
                not auth_activities and
                account.activity_type == activity.activity_type
            ):
                self.activity_id = activity_id
            elif auth_activities:
                self.activity_id = auth_activities[0].id
            else:
                self.activity_id = False
