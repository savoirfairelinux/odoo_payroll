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

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


class HrLeaveAccrualLineCash(models.Model):
    """Leave Accrual Line Cash"""

    _name = 'hr.leave.accrual.line.cash'
    _inherit = 'hr.leave.accrual.line'
    _description = _(__doc__)

    amount = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Payroll'),
    )
    accrual_id = fields.Many2one(
        'hr.leave.accrual',
        'Leave Accrual',
        ondelete='restrict',
        required=True,
    )
    payslip_id = fields.Many2one(
        'hr.payslip',
        'Payslip',
        ondelete='cascade',
    )
    payslip_line_id = fields.Many2one(
        'hr.payslip.line',
        'Payslip Line',
        ondelete='cascade',
        readonly=True,
    )
    state = fields.Selection(
        string='State',
        related='payslip_id.state',
        readonly=True,
        store=True,
    )
    is_refund = fields.Boolean(
        'Is Refund',
        related='payslip_id.credit_note',
        readonly=True,
        store=True,
    )

    @api.model
    def create(self, vals):
        res = super(HrLeaveAccrualLineCash, self).create(vals)

        if not self.env.context.get('disable_leave_accrual_update'):
            res.accrual_id.update_total_cash()

        return res

    @api.multi
    def write(self, vals):
        res = super(HrLeaveAccrualLineCash, self).write(vals)
        if not self.env.context.get('disable_leave_accrual_update'):
            self.mapped('accrual_id').update_total_cash()
        return res

    @api.multi
    def unlink(self):
        accruals = self.mapped('accrual_id')
        res = super(HrLeaveAccrualLineCash, self).unlink()

        accruals.refresh()
        accruals.update_total_cash()

        return res
