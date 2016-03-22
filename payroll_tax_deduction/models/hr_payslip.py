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


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    deduction_line_ids = fields.One2many(
        'hr.payslip.deduction.line',
        'payslip_id',
        'Income Tax Deductions',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=True,
    )

    @api.multi
    def compute_sheet(self):
        self.compute_deductions()
        super(HrPayslip, self).compute_sheet()

    @api.one
    def compute_deductions(self):
        """
        Compute the deductions on the payslip.
        """
        self.deduction_line_ids.filtered(
            lambda d: d.source == 'employee').unlink()

        pays_per_year = self.pays_per_year

        date_reference = self.date_payment

        deductions = self.employee_id.deduction_ids.filtered(
            lambda d: d.date_start <= date_reference <= d.date_end)

        self.write({
            'deduction_line_ids': [(0, 0, {
                'category_id': d.category_id.id,
                'source': 'employee',
                'amount': d.amount / pays_per_year
                if d.amount_type == 'annual' else d.amount,
            }) for d in deductions]
        })
