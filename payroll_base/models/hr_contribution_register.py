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

from openerp import models, fields, _


class ContributionRegister(models.Model):
    """Contribution Register"""

    _name = 'hr.contribution.register'
    _description = _(__doc__)

    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id.id,
    )
    partner_id = fields.Many2one(
        'res.partner',
        'Partner'
    )
    name = fields.Char(
        'Name',
        required=True,
        readonly=False
    )
    register_line_ids = fields.One2many(
        'hr.payslip.line',
        'register_id',
        'Register Line',
        readonly=True
    )
    note = fields.Text(
        'Description'
    )
