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

from openerp import api, models, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    benefit_line_ids = fields.One2many(
        'hr.payslip.benefit.line',
        'payslip_id',
        'Employee Benefits',
        readonly=True, states={'draft': [('readonly', False)]},
        copy=True,
    )

    @api.multi
    def _search_benefits(self):
        """
        Search employee benefits to be added on the payslip

        This method is meant to be inherited in other modules
        in order to add benefits from other sources.
        """
        self.ensure_one()
        return self.contract_id.benefit_line_ids

    @api.multi
    def button_compute_benefits(self):
        self.compute_benefits()

    @api.one
    def compute_benefits(self):
        """
        Compute the employee benefits on the payslip.

        This method can be called from inside a salary rule.

        Exemple
        -------
        payslip.compute_benefits()

        This is required when the benefits are based on the value
        of one or more salary rules.

        The module hr_employee_benefit_percent implements that
        functionnality.
        """
        for benefit_line in self.benefit_line_ids:
            if benefit_line.source == 'contract':
                benefit_line.unlink()

        benefits = self._search_benefits()

        # Compute the amounts for each employee benefit
        benefits.compute_amounts(self)

        # If the method is called from a salary rule.
        # It is important to call refresh() so that the record set
        # will contain the benefits computed above.
        self.refresh()
