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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    hr_period_id = fields.Many2one(
        'hr.period',
        string='Period',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    @api.one
    @api.constrains('hr_period_id', 'company_id')
    def _check_period_company(self):
        if self.hr_period_id:
            if self.hr_period_id.company_id != self.company_id:
                raise ValidationError(
                    "The company on the selected period must "
                    "be the same as the company on the "
                    "payslip."
                )
        return True

    @api.onchange('company_id', 'contract_id')
    def onchange_company_id(self):
        if self.company_id and self.contract_id:

            period = self.env['hr.period'].get_next_period(
                self.company_id.id, self.contract_id.schedule_pay)

            self.hr_period_id = period.id if period else False

    @api.onchange('hr_period_id')
    def onchange_hr_period_id(self):
        if self.hr_period_id:
            period = self.hr_period_id
            self.date_from = period.date_start
            self.date_to = period.date_stop
            self.date_payment = period.date_payment

    @api.onchange('payslip_run_id')
    def onchange_payslip_run_id(self):
        super(HrPayslip, self).onchange_payslip_run_id()

        payslip_run = self.payslip_run_id

        if payslip_run:
            period = payslip_run.hr_period_id
            self.hr_period_id = period.id
            if period:
                self.name = _('Salary Slip of %s for %s') % (
                    self.employee_id.name, period.name)
