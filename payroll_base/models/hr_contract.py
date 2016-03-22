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

from openerp import fields, models, api, _


class HrContract(models.Model):

    _inherit = 'hr.contract'

    struct_id = fields.Many2one(
        'hr.payroll.structure',
        'Salary Structure',
    )
    schedule_pay = fields.Selection(
        lambda self: self.get_schedule_selection(),
        'Scheduled Pay',
        select=True,
        default='monthly',
    )
    pays_per_year = fields.Float(
        'Pays Per Year',
        compute='_get_pays_per_year',
        store=True,
        readonly=True,
    )

    @api.model
    def get_schedule_selection(self):
        return [
            ('monthly', _('Monthly')),
            ('quarterly', _('Quarterly')),
            ('semi-annually', _('Semi-annually')),
            ('annually', _('Annually')),
            ('weekly', _('Weekly')),
            ('bi-weekly', _('Bi-weekly')),
            ('bi-monthly', _('Bi-monthly')),
            ('semi-monthly', _('Semi-monthly')),
        ]

    @api.multi
    def get_all_structures(self):
        """
        :return: record set of hr.payroll.structure
        """
        structures = self.mapped('struct_id')
        return structures.get_parent_structures()

    @api.one
    @api.depends('schedule_pay')
    def _get_pays_per_year(self):
        """
        :param ids: ID of contract
        :return: The number of pays per year
        """
        schedule_pay = {
            'daily': 365,
            'weekly': 52,
            'bi-weekly': 26,
            'semi-monthly': 24,
            'monthly': 12,
            'bi-monthly': 6,
            'quarterly': 4,
            'semi-annually': 2,
            'annually': 1,
        }

        if (
            self.schedule_pay and
            schedule_pay.get(self.schedule_pay)
        ):
            self.pays_per_year = schedule_pay[self.schedule_pay]
