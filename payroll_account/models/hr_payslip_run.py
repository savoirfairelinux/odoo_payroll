# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2015 Savoir-faire Linux
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

from openerp import api, fields, models


class HrPayslipRun(models.Model):

    _inherit = 'hr.payslip.run'

    journal_id = fields.Many2one(
        'account.journal',
        'Salary Journal',
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True,
        default=lambda self: self.env.user.company_id.payroll_journal_id,
    )

    @api.onchange('company_id')
    def onchange_company_id(self):
        super(HrPayslipRun, self).onchange_company_id()
        self.journal_id = self.company_id.payroll_journal_id.id
