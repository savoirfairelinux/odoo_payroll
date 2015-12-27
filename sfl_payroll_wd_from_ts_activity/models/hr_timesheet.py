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

from openerp import api, models


class HrTimesheet(models.Model):

    _inherit = 'hr.analytic.timesheet'

    @api.multi
    def worked_days_mapping(self):
        """
        This method is entended to be inherited.

        It maps a single timesheet record to a dict of field values
        that would be used to generate a worked_days record.
        """
        self.ensure_one()
        res = super(HrTimesheet, self).worked_days_mapping()
        res['activity_id'] = self.activity_id.id
        return res
