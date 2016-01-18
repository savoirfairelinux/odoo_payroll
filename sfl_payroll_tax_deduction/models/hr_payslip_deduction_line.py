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

from openerp import fields, models, _


class HrPayslipDeductionLine(models.Model):
    """Pay Slip Deduction Line"""

    _name = 'hr.payslip.deduction.line'
    _decription = _(__doc__)

    payslip_id = fields.Many2one(
        'hr.payslip',
        'Payslip',
        required=True,
        ondelete='cascade',
    )
    category_id = fields.Many2one(
        'hr.deduction.category',
        'Deduction',
        required=True,
    )
    amount = fields.Float(
        'Amount'
    )
    source = fields.Selection(
        [
            ('employee', 'From Employee Profile'),
            ('manual', 'Added Manually'),
        ],
        readonly=True,
        required=True,
        string='Type',
        type='char',
        default='manual',
    )
