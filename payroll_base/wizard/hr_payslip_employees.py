# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from openerp.exceptions import ValidationError


class HrPayslipEmployee(models.TransientModel):
    """Payslip Run Wizard"""

    _name = 'hr.payslip.employees'
    _description = _(__doc__)

    payslip_run_id = fields.Many2one(
        'hr.payslip.run',
        'Active Payslip Run',
    )

    employee_ids = fields.Many2many(
        'hr.employee',
        'hr_employee_group_rel',
        'payslip_id',
        'employee_id',
        'Employees',
    )

    payslip_ids = fields.Many2many(
        'hr.payslip',
        string='Generated Payslips',
    )

    @api.multi
    def compute_sheet(self):
        self.ensure_one()

        context = self.env.context
        active_id = context.get('active_id')
        self.write({'payslip_run_id': active_id})
        payslip_run = self.env['hr.payslip.run'].browse(active_id)

        if not self.employee_ids:
            raise ValidationError(
                _("You must select employee(s) to generate payslip(s)."))

        payslip_model = self.env['hr.payslip']
        payslips = self.env['hr.payslip']

        for employee in self.employee_ids:

            new_payslip = payslip_model.create({
                'employee_id': employee.id,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
            })

            new_payslip.onchange_payslip_run_id()

            payslips += new_payslip

        self.payslip_ids = [(6, 0, payslips.ids)]

        self.action_before_computing_sheets()
        payslips.compute_sheet()

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_before_computing_sheets(self):
        return True
