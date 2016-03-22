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

from openerp import fields, models


class res_company(models.Model):
    _inherit = 'res.company'

    qc_cnt_debit_account = fields.Many2one(
        'account.account',
        'CNT - Debit Account',
        help="Expense account for the CNT contribution."
    )

    qc_cnt_credit_account = fields.Many2one(
        'account.account',
        'CNT - Credit Account',
        help="Account payable for the CNT contribution."
    )

    qc_wsdrf_debit_account = fields.Many2one(
        'account.account',
        'WSDRF - Debit Account',
        help="Expense account for the WSDRF contribution."
    )

    qc_wsdrf_credit_account = fields.Many2one(
        'account.account',
        'WSDRF - Credit Account',
        help="Account payable for the WSDRF contribution."
    )

    qc_wsdrf_reported_account = fields.Many2one(
        'account.account',
        'WSDRF - Reported Expenses Account',
        help="Account for the expenses eligible to the WSDRF "
        "reported from one year to another. "
        "Must be an asset account."
    )
