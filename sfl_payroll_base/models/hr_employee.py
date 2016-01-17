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

from openerp import api, fields, models


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    @api.one
    def _payslip_count(self):
        self.payslip_count = len(self.slip_ids)

    slip_ids = fields.One2many(
        'hr.payslip',
        'employee_id',
        'Payslips',
        required=False,
        readonly=True
    )
    payslip_count = fields.Integer(
        compute='_payslip_count',
        string='Payslips',
    )
