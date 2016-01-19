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

from openerp import api, models, _
from openerp.exceptions import ValidationError


class HrPayslipEmployee(models.TransientModel):

    _inherit = 'hr.payslip.employees'

    @api.multi
    def compute_sheet(self):
        self.ensure_one()

        active_id = self.env.context.get('active_id')
        payslip_run = self.env['hr.payslip.run'].browse(active_id)
        if not payslip_run.journal_id:
            raise ValidationError(_(
                'The journal is not set on the payslip run.'
            ))

        ctx = dict(self.env.context)
        ctx['journal_id'] = payslip_run.journal_id.id
        self = self.with_context(ctx)

        return super(HrPayslipEmployee, self).compute_sheet()
