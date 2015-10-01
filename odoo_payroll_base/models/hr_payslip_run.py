# -*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

from dateutil.relativedelta import relativedelta

from openerp import fields, models, api


class hr_payslip_run(models.Model):
    _name = 'hr.payslip.run'
    _description = 'Payslip Batches'

    name = fields.Char(
        'Name',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
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
        default=lambda self: fields.Date.context_today(self),
    )
    date_end = fields.Date(
        'Date To',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: fields.Date.context_today(self) +
        relativedelta(months=+1, day=1, days=-1),
    )
    credit_note = fields.Boolean(
        'Credit Note',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="If its checked, indicates that all payslips generated "
        "from here are refund payslips."
    )

    @api.multi
    def draft_payslip_run(self):
        return self.write({'state': 'draft'})

    @api.multi
    def close_payslip_run(self):
        return self.write({'state': 'close'})
