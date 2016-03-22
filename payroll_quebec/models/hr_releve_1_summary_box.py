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

from openerp import api, fields, models, _


class HrReleve1SummaryBox(models.Model):
    """Releve 1 Summary Box"""

    _name = 'hr.releve_1.summary.box'
    _description = _(__doc__)

    name = fields.Char(
        'Name',
        required=True
    )
    active = fields.Boolean(
        'Active',
        default=True,
    )
    child_ids = fields.Many2many(
        'hr.releve_1.box',
        'hr_releve_1_summary_total_box_rel',
        string='Related Releve 1 Boxes that will be summed in the'
        'Summary Box.',
    )

    @api.multi
    def compute_amount(self, slip_ids):
        """
        Return the amount of a Releve 1 Summary box from the given
        list of slips related to the summary

        :type slip_ids: hr.releve_1 id list
        :rtype: float
        """
        self.ensure_one()

        amounts = self.env['hr.releve_1.amount'].search([
            ('slip_id', 'in', slip_ids),
            ('box_id', 'in', self.child_ids.ids),
        ])

        return sum(a.amount for a in amounts)
