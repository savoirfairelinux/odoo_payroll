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


class HrEmployeeBenefit(models.Model):

    _inherit = 'hr.employee.benefit'

    job_id = fields.Many2one(
        'hr.job',
        'Job',
        ondelete='cascade',
        index=True
    )

    @api.multi
    def compute_amounts(self, payslip):
        other_benefits = self.filtered(
            lambda b: b.amount_type != 'per_hour')

        benefits_per_hour = self - other_benefits

        super(HrEmployeeBenefit, other_benefits).compute_amounts(payslip)

        # Case where the benefit is per_hour
        for benefit in benefits_per_hour:

            # Case where the benefit is related to a single job
            if benefit.job_id:
                worked_days = payslip.worked_days_line_ids.filtered(
                    lambda wd: wd.activity_id.job_id == benefit.job_id)

            # Case where the benefit is related to a contract
            # In that case, the benefit applies for all jobs
            elif benefit.contract_id:
                worked_days = payslip.worked_days_line_ids

            else:
                worked_days = self.env['hr.payslip.worked_days']

            for wd in worked_days:
                benefit.rate_id.compute_amounts_per_hour(wd)
