# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux
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

from openerp import api, fields, models

to_string = fields.Date.to_string


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    @api.multi
    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()
        self.compute_ytd_amounts()
        return res

    @api.one
    def compute_ytd_amounts(self):
        if not self.line_ids:
            return

        query = (
            """SELECT pl_1.id, sum(
                case when p.credit_note then -pl_2.amount else pl_2.amount end)
            FROM hr_payslip_line pl_1, hr_payslip_line pl_2, hr_payslip p
            WHERE pl_1.id IN %(payslip_line_ids)s
            AND pl_1.salary_rule_id = pl_2.salary_rule_id
            AND pl_2.slip_id = p.id
            AND p.employee_id = %(employee_id)s
            AND p.company_id = %(company_id)s
            AND (p.state = 'done' OR p.id = %(payslip_id)s)
            AND %(date_from)s <= p.date_payment
            AND p.date_payment <= %(date_to)s
            GROUP BY pl_1.id
            """)

        date_payment = fields.Date.from_string(self.date_payment)
        date_from = fields.Date.to_string(
            datetime(date_payment.year, 1, 1))

        cr = self.env.cr

        cr.execute(query, {
            'date_from': date_from,
            'date_to': self.date_payment,
            'payslip_line_ids': tuple(self.line_ids.ids),
            'employee_id': self.employee_id.id,
            'company_id': self.company_id.id,
            'payslip_id': self.id,
        })

        res = cr.fetchall()

        line_model = self.env['hr.payslip.line']

        for (line_id, amount_ytd) in res:
            line = line_model.browse(line_id)
            line.amount_ytd = amount_ytd

    @api.multi
    def ytd_amount(self, code):
        """
        Get the total amount since the beginning of the year
        of a given salary rule code.

        :param code: salary rule code
        :return: float
        """
        self.ensure_one()

        date_slip = fields.Date.from_string(self.date_payment)
        date_from = to_string(datetime(date_slip.year, 1, 1))

        query = (
            """SELECT sum(
                case when p.credit_note then -pl.amount else pl.amount end)
            FROM hr_payslip_line pl, hr_payslip p
            WHERE pl.slip_id = p.id
            AND pl.code = %(code)s
            AND p.employee_id = %(employee_id)s
            AND p.company_id = %(company_id)s
            AND p.state = 'done'
            AND %(date_from)s <= p.date_payment
            AND p.date_payment <= %(date_to)s
            """
        )

        cr = self.env.cr

        cr.execute(query, {
            'date_from': date_from,
            'date_to': self.date_payment,
            'company_id': self.company_id.id,
            'employee_id': self.employee_id.id,
            'code': code,
        })

        return cr.fetchone()[0] or 0
