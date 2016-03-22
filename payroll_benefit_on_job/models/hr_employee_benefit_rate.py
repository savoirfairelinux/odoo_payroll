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


class HrEmployeeBenefitRate(models.Model):
    _inherit = 'hr.employee.benefit.rate'

    def get_all_amount_types(self, cr, uid, context=None):
        res = super(HrEmployeeBenefitRate, self).get_all_amount_types(
            cr, uid, context=context)

        res.append(('per_hour', _('Per Worked Hour')))

        return res

    @api.multi
    def compute_amounts_per_hour(self, worked_days):
        """
        Compute the amounts of benefit that are based on worked hours.
        """
        worked_days.ensure_one()

        for rate in self:

            rate_lines = rate.line_ids.filtered(
                lambda l:
                (not l.date_end or worked_days.date <= l.date_end) and
                l.date_start <= worked_days.date
            )

            for line in rate_lines:

                self.env['hr.payslip.benefit.line'].create({
                    'payslip_id': worked_days.payslip_id.id,
                    'employer_amount': line.employer_amount *
                    worked_days.number_of_hours,
                    'employee_amount': line.employee_amount *
                    worked_days.number_of_hours,
                    'category_id': line.category_id.id,
                    'source': 'contract',
                })
