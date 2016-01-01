# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
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

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


class HrLeaveAccrual(models.Model):
    """Leave Accrual"""

    _name = 'hr.leave.accrual'
    _description = _(__doc__)

    leave_type_id = fields.Many2one(
        'hr.holidays.status',
        string='Leave Type',
        ondelete='restrict',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        required=True,
        ondelete='cascade',
    )
    line_ids = fields.One2many(
        'hr.leave.accrual.line',
        'accrual_id',
        string='Accrual Lines',
    )
    total_cash = fields.Float(
        'Cash Accruded',
        readonly=True,
        digits_compute=dp.get_precision('Payroll'),
    )
    total_hours = fields.Float(
        'Hours Accruded',
        readonly=True,
        digits_compute=dp.get_precision('Payroll Hours'),
    )

    @api.one
    def name_get(self):
        return (self.id, '%s - %s' % (
            self.leave_type_id.name, self.employee_id.name))

    @api.one
    def update_totals(self):
        """
        Compute the total of the leave accrual.

        This method would be a bottle neck in the application if it were
        triggered every time a line is inserted in the accrual
        in a payslip run. This is why we defere the action when the
        payslip is computing leave accruals.
        """
        if self.env.context.get('disable_leave_accrual_update'):
            return

        total_hours = 0
        total_cash = 0

        query = (
            """SELECT l.is_refund, sum(l.amount_cash), sum(l.amount_hours)
            FROM hr_leave_accrual a, hr_leave_accrual_line l
            WHERE l.accrual_id = a.id AND a.id = %s
            AND (l.state = 'done' or l.source != 'payslip')
            GROUP BY l.is_refund
            """)

        cr = self.env.cr
        cr.execute(query, (self.id, ))

        for (is_refund, amount_cash, amount_hours) in cr.fetchall():

            if is_refund:
                total_cash -= amount_cash or 0
                total_hours -= amount_hours or 0
            else:
                total_cash += amount_cash or 0
                total_hours += amount_hours or 0

        self.write({
            'total_hours': total_hours,
            'total_cash': total_cash,
        })

        self.refresh()

    @api.multi
    def sum_leaves_available(self, date, in_cash=False):
        self.ensure_one()
        return self.total_cash if in_cash else self.total_hours
