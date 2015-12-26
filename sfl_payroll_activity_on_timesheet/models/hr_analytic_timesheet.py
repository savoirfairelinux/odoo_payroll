# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Savoir-faire Linux. All Rights Reserved.
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

from openerp import api, fields, models


class HrAnalyticTimesheet(models.Model):
    _inherit = 'hr.analytic.timesheet'
    activity_id = fields.Many2one(
        'hr.activity',
        'Activity',
        required=True,
    )

    @api.multi
    def on_change_account_id(
        self, account_id, user_id=False, activity_id=False
    ):
        # on_change_account_id in module hr_timesheet_invoice does
        # not accept the context argument, so we don't pass it with super
        res = super(HrAnalyticTimesheet, self).on_change_account_id(
            account_id, user_id=user_id)

        if 'value' not in res:
            res['value'] = {}

        # If an activity and an account are given, check if the activity
        # is authorized for the account. If the activity is authorized,
        # return the same activity_id.
        if not activity_id:
            res['value']['activity_id'] = False

        elif account_id:
            account = self.env['account.analytic.account'].browse(account_id)

            auth_activities = account.authorized_activity_ids
            activity = self.env['hr.activity'].browse(activity_id)

            if activity in auth_activities or (
                not auth_activities and
                account.activity_type == activity.activity_type
            ):
                res['value']['activity_id'] = activity_id
            elif auth_activities:
                res['value']['activity_id'] = auth_activities[0].id
            else:
                res['value']['activity_id'] = False

        return res
