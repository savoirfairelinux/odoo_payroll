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


class HrCRAT4SummaryBox(models.Model):
    """T4 Summary Box"""

    _name = 'hr.cra.t4.summary.box'
    _description = _(__doc__)

    name = fields.Char(
        'Name',
        required=True
    )
    active = fields.Boolean(
        'Active',
        default=True,
    )
    xml_tag = fields.Char(
        'XML Tag',
        required=True
    )
    child_ids = fields.Many2many(
        'hr.cra.t4.box',
        'hr_t4_summary_total_box_rel',
        string='Related T4 Boxes',
    )

    @api.multi
    def compute_amount(self, slip_ids):
        """
        Return the amount of a T4 Summary box from the given
        list of slips related to the summary

        :type slip_ids: hr.cra.t4 id list
        :rtype: float
        """
        self.ensure_one()

        child_boxes = self.child_ids

        child_amounts = self.env['hr.cra.t4.amount'].search([
            ('slip_id', 'in', slip_ids),
            ('box_id', 'in', child_boxes.ids),
        ])

        return sum(a.amount for a in child_amounts)
