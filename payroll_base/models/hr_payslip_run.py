# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>)
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
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models, _


class HrPayslipRun(models.Model):
    """Payslip Batches"""

    _name = 'hr.payslip.run'
    _description = _(__doc__)

    name = fields.Char(
        'Name',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'hr.payslip.run')
    )
    slip_ids = fields.One2many(
        'hr.payslip',
        'payslip_run_id',
        'Payslips',
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('close', 'Close'),
        ],
        'Status',
        select=True,
        readonly=True,
        copy=False,
        default='draft',
    )
    date_start = fields.Date(
        'Date From',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: datetime.now(),
    )
    date_end = fields.Date(
        'Date To',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: datetime.now() +
        relativedelta(months=+1, days=-1),
    )
    date_payment = fields.Date(
        'Date of Payment',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: datetime.now() +
        relativedelta(months=+1, days=-1),
    )
    credit_note = fields.Boolean(
        'Credit Note',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="If its checked, indicates that all payslips generated "
        "from here are refund payslips."
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        states={'close': [('readonly', True)]},
        default=lambda self: self.env.user.company_id
    )

    @api.multi
    def draft_payslip_run(self):
        return self.write({'state': 'draft'})

    @api.multi
    def close_payslip_run(self):
        return self.write({'state': 'close'})

    @api.one
    def button_confirm_slips(self):
        for slip in self.slip_ids:
            slip.process_sheet()

    @api.multi
    @api.returns('hr.employee')
    def get_employees(self):
        self.ensure_one()
        return self.env['hr.employee'].search([
            ('company_id', '=', self.company_id.id),
        ])

    @api.onchange('company_id')
    def onchange_company_id(self):
        return

    @api.multi
    def get_payslip_employees_wizard(self):
        self.ensure_one()

        view_ref = self.env.ref(
            'payroll_base.view_hr_payslip_by_employees')

        employees = self.get_employees()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Payslips'),
            'res_model': 'hr.payslip.employees',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_ref.id,
            'target': 'new',
            'context': {
                'default_company_id': self.company_id.id,
                'default_employee_ids': [(6, 0, employees.ids)],
            }
        }
