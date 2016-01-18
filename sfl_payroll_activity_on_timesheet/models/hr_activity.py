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

from datetime import datetime

from openerp import fields, models
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


to_string = fields.Date.to_string


class HrActivity(models.Model):
    _inherit = 'hr.activity'

    def _get_authorized_user_ids(self):
        """
        Get the ids of users related to an employee that occupies a job
        position related to an activity.
        """
        now = to_string(datetime.now())

        for activity in self:
            if activity.activity_type != 'job':
                activity.authorized_user_ids = False

            else:
                contract_jobs = activity.job_id.contract_job_ids.filtered(
                    lambda j: j.contract_id.date_start <= now and (
                        not j.contract_id.date_end or
                        now <= j.contract_id.date_end
                    ))

                users = contract_jobs.mapped('contract_id.employee_id.user_id')
                activity.authorized_user_ids = users.ids

    def _search_activities_from_user(self, operator=None, value=None):
        """
        Search the activities from a given user id

        This method is called by a view to get the job positions of
        an employee
        """
        context = self.env.context

        # The context should contain the user id of the employee
        # to whom the timesheet belongs
        if 'user_id' in context:
            user = self.env['res.users'].browse(context['user_id'])
            if not user.employee_ids:
                return []

            employee = user.employee_ids[0]
        else:
            return []

        if not employee.contract_id:
            raise ValidationError(_(
                "There is no available contract for employee %s." %
                employee.name))

        activities = self.env['hr.activity']

        account_model = self.env['account.analytic.account']
        account = (
            account_model.browse(context['account_id'])
            if 'account_id' in context else None
        )

        # Get the activities related to the jobs
        # on the employee's contract
        if not account or account.activity_type == 'job':
            activities += employee.contract_id.contract_job_ids.mapped(
                'job_id.activity_ids')

        if not account or account.activity_type == 'leave':
            activities += self.env['hr.activity'].search(
                [('activity_type', '=', 'leave')])

        # Return all activities if no account was given in context
        if not account or not account.authorized_activity_ids:
            return [('id', 'in', activities.ids)]

        auth_activities = activities & account.authorized_activity_ids

        return [('id', 'in', auth_activities.ids)]

    authorized_user_ids = fields.Many2many(
        compute='_get_authorized_user_ids',
        search='_search_activities_from_user',
        comodel_name='res.users',
        string='Authorized Users',
    )
    authorized_account_ids = fields.Many2many(
        'account.analytic.account',
        'account_analytic_activity_rel',
        'activity_id',
        'analytic_account_id',
        'Authorized Accounts',
    )
