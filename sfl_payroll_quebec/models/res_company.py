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
from openerp.exceptions import ValidationError
from itertools import permutations


class ResCompany(models.Model):
    _inherit = 'res.company'

    rq_payroll_id = fields.Char(
        'Revenu Québec Identification Number',
        help="Must contain 10 numeric caracters.",
    )

    rq_payroll_file_number = fields.Char(
        'Revenu Québec File Number',
        help="Must contain 4 numeric caracters.",
    )

    rq_first_slip_number = fields.Integer(
        'First Sequencial Number',
    )

    rq_last_slip_number = fields.Integer(
        'Last Sequencial Number',
    )

    slip_transmission_type = fields.Selection(
        [('post', 'Send By Post')],
        required=True,
        type="char",
        string="Slip Transmission Type",
        default='post',
    )

    rq_preparator_number = fields.Char(
        'Revenu Québec Preparator Number',
    )

    csst_rate_ids = fields.One2many(
        'hr.qc.rate',
        'company_id',
        string="CSST Rates",
        domain=[('contribution_type', '=', 'csst')],
    )
    hsf_rate_ids = fields.One2many(
        'hr.qc.rate',
        'company_id',
        string="HSF Rates",
        domain=[('contribution_type', '=', 'hsf')],
    )

    @api.constrains('csst_rate_ids', 'hsf_rate_ids')
    def _check_overlapping_csst_hsf_rates(self):
        """
        Checks if a class has two rates that overlap in time.
        """
        for company in self:
            for rate_list in [company.csst_rate_ids, company.hsf_rate_ids]:
                for r1, r2 in permutations(rate_list, 2):
                    if (
                        r1.date_to and
                        r1.date_from <= r2.date_from <= r1.date_to
                    ) or (
                        not r1.date_to and
                        r1.date_from <= r2.date_from
                    ):
                        raise ValidationError(
                            "You cannot have overlapping CSST or HSF rates"
                        )

        return True

    @api.multi
    def get_next_rq_sequential_number(self, slip_model, year):
        """
        Create a sequential number as required by Revenu Québec.

        Each number can be used one time each year.

        The range of number is defined in the company model.
        It is assigned to the company by Revenu Québec.
        """
        self.ensure_one()

        first_number = self.rq_first_slip_number
        last_number = self.rq_last_slip_number

        if not first_number or not last_number:
            raise ValidationError(_(
                "Your sequence number range for Revenu Québec "
                "is incorrectly set"))

        # Get the model of the required fiscal slip
        slips = self.env[slip_model].search([
            ('company_id', '=', self.id),
            ('year', '=', year),
            ('number', '!=', False),
        ])

        number = first_number

        if slips:
            assigned_numbers = [
                # we get the first 8 digits of the number
                # the ninth digit is a validation digit
                # so we remove it
                int((float(slip.number) / 10) // 1) for slip in
                slips
            ]

            while number in assigned_numbers:
                # we find a number that is not already assigned
                number += 1

                if number > last_number:
                    raise ValidationError(_(
                        "You have already used all your sequential "
                        "numbers assigned by Revenu Québec"))

        num_a = float(number) / 7
        # Here, we need 2 decimals
        # round function do what we need here, because
        # round(2.539, 2) * 7 would give 2.54 * 7
        # we need 2.5a * 7
        num_b = (num_a % 1 - num_a % 0.01) * 7
        num_c = round(num_b, 0)

        return number * 10 + int(num_c)

    @api.multi
    def get_qc_rate(self, date, contribution_type):
        self.ensure_one()

        if contribution_type == 'csst':
            rates = self.csst_rate_ids
        elif contribution_type == 'hsf':
            rates = self.hsf_rate_ids

        for rate in rates:
            if rate.date_from <= date <= rate.date_to:
                return rate.rate / 100

        return False
