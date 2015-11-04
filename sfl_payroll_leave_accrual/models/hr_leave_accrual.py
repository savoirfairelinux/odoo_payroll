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
    total_monetary = fields.Float(
        'monetary Accruded',
        readonly=True,
    )
    total_hours = fields.Float(
        'Hours Accruded',
        readonly=True,
    )

    @api.multi
    def get_approved_lines(self):
        """
        Get lines of leave accruals entered mannually plus those
        related to an approved payslip
        """
        self.ensure_one()
        return self.mapped('line_ids').filtered(
            lambda l: not l.payslip_id or l.state in ['done'])

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
        total_monetary = 0

        query = (
            """SELECT l.amount_type, l.is_refund, sum(l.amount)
            FROM hr_leave_accrual a, hr_leave_accrual_line l
            WHERE l.accrual_id = a.id AND a.id = %s
            AND (l.state = 'done' or l.source != 'payslip')
            GROUP BY l.amount_type, l.is_refund
            """)

        cr = self.env.cr
        cr.execute(query, (self.id, ))

        for (amount_type, is_refund, amount) in cr.fetchall():

            if is_refund:
                if amount_type == 'monetary':
                    total_monetary -= amount
                elif amount_type == 'hours':
                    total_hours -= amount
            else:
                if amount_type == 'monetary':
                    total_monetary += amount
                elif amount_type == 'hours':
                    total_hours += amount

        self.write({
            'total_hours': total_hours,
            'total_monetary': total_monetary,
        })
