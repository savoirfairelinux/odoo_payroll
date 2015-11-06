# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#    Author Nikolina Todorova <nikolina.todorova@initos.com>
#    Copyright (C) 2015 Savoir-faire Linux
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

from openerp import models, fields, api, _
from datetime import datetime
from openerp.exceptions import ValidationError


class HrPublicHolidays(models.Model):
    _name = 'hr.holidays.public'
    _description = 'Public Holidays'
    _rec_name = 'year'
    _order = 'year'

    year = fields.Char(
        "Calendar Year",
        required=True,
        help="Enter the year with a numeric value "
        "e.g. '2015' or '2016'."
    )
    line_ids = fields.One2many(
        'hr.holidays.public.line',
        'holidays_id',
        'Holiday Dates'
    )
    country_id = fields.Many2one(
        'res.country',
        'Country',
        required=True,
    )

    @api.one
    @api.constrains('year')
    def _check_year(self):
        try:
            datetime.strptime(self.year, '%Y')
        except:
            raise ValidationError(
                _("The year %s must be written with a numeric value "
                  "e.g. '2015' or '2016'.") % self.year)

    _sql_constraints = [
        ('year_unique',
         'UNIQUE(year,country_id)',
         _('Duplicate year and country!')),
    ]

    @api.model
    @api.returns('hr.holidays.public.line')
    def get_holidays_lines(self, date_from, date_to, partner_id):
        """
        Get a recordset of hr.holidays.public.line
        for the specified date interval and partner

        The method uses the partner's address to find the country and
        state.

        :param date_from: string date
        :param date_from: string date

        :return: recordset of hr.holidays.public.line
        """
        partner = self.env['res.partner'].browse(partner_id)

        if not partner.country_id:
            raise ValidationError(
                _('The country of %s is not set.') % partner.country_id.name)

        return self.env['hr.holidays.public.line'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('country_id', '=', partner.country_id.id),
            '|',
            ('state_ids', '=',
                partner.state_id and partner.state_id.id or False),
            ('state_ids', '=', False),
        ])
