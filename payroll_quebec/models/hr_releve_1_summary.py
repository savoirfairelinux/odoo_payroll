# -*- coding:utf-8 -*-#########################################################
#
#    Copyright (C) 2016 Savoir-faire Linux. All Rights Reserved.
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

from datetime import datetime

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp


FLOAT_PARAM = {
    'readonly': True,
    'states': {'draft': [('readonly', False)]},
    'digits_compute': dp.get_precision('Payroll'),
    'default': 0,
}

FUNCTION_PARAM = {
    'readonly': True,
    'digits_compute': dp.get_precision('Payroll'),
    'default': 0,
    'store': True,
}


class HrReleve1Summary(models.Model):
    """Relevé 1 Summary"""

    _name = 'hr.releve_1.summary'
    _description = _(__doc__)

    _inherit = 'hr.qc.summary'

    @api.multi
    def get_payslips(self):
        self.ensure_one()

        structure = self.env.ref('payroll_quebec.hr_structure_qc')
        structure_ids = structure.get_children_recursively().ids

        year = int(self.year)
        date_from = datetime(year, 1, 1).strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime(year, 12, 31).strftime(
            DEFAULT_SERVER_DATE_FORMAT)

        return self.env['hr.payslip'].search([
            ('date_payment', '>=', date_from),
            ('date_payment', '<=', date_to),
            ('company_id', '=', self.company_id.id),
            ('struct_id', 'in', structure_ids),
            ('state', '=', 'done'),
        ])

    @api.depends('qpp_amount_ee', 'qpp_amount_er')
    def _compute_qpp_amount_total(self):
        for s in self:
            s.qpp_amount_total = s.qpp_amount_ee + s.qpp_amount_er

    @api.depends('qpip_amount_ee', 'qpip_amount_er')
    def _compute_qpip_amount_total(self):
        for s in self:
            s.qpip_amount_total = s.qpip_amount_ee + s.qpip_amount_er

    @api.depends('qit_amount_1', 'qit_amount_2')
    def _compute_qit_amount_total(self):
        for s in self:
            s.qit_amount_total = s.qit_amount_1 + s.qit_amount_2

    @api.depends('qpp_amount_total', 'qpip_amount_total', 'qit_amount_total')
    def _compute_sub_total_contribution(self):
        for s in self:
            s.sub_total_contribution = (
                s.qpp_amount_total + s.qpip_amount_total + s.qit_amount_total)

    @api.depends('sub_total_contribution', 'sub_total_remitted')
    def _compute_sub_total_payable(self):
        for s in self:
            s.sub_total_payable = (
                s.sub_total_contribution - s.sub_total_remitted)

    @api.depends(
        'hsf_salaries', 'hsf_exemption_amount', 'hsf_contribution_rate')
    def _compute_hsf_amount_before_reduction(self):
        for s in self:
            s.hsf_amount_before_reduction = (
                s.hsf_salaries - s.hsf_exemption_amount
            ) * s.hsf_contribution_rate / 100

    @api.depends('hsf_reduction_basis', 'hsf_reduction_rate')
    def _compute_hsf_reduction_amount(self):
        for s in self:
            s.hsf_reduction_amount = (
                s.hsf_reduction_basis * s.hsf_reduction_rate / 100)

    @api.depends(
        'hsf_amount_before_reduction',
        'hsf_reduction_amount', 'hsf_amount_remitted')
    def _compute_hsf_amount_payable(self):
        for s in self:
            s.hsf_amount_payable = (
                s.hsf_amount_before_reduction - s.hsf_reduction_amount -
                s.hsf_amount_remitted)

    @api.depends('cnt_salaries', 'cnt_rate')
    def _compute_cnt_amount_payable(self):
        for s in self:
            s.cnt_amount_payable = (
                s.cnt_salaries * s.cnt_rate / 100)

    @api.depends('wsdrf_salaries', 'wsdrf_rate')
    def _compute_wsdrf_amount_before_expenses(self):
        for s in self:
            s.wsdrf_amount_before_expenses = (
                s.wsdrf_salaries * s.wsdrf_rate / 100)

    @api.depends('wsdrf_previous_reported', 'wsdrf_expenses_current')
    def _compute_wsdrf_expenses_available(self):
        for s in self:
            s.wsdrf_expenses_available = (
                s.wsdrf_previous_reported +
                s.wsdrf_expenses_current)

    @api.depends('wsdrf_expenses_available', 'wsdrf_expenses')
    def _compute_wsdrf_reported(self):
        for s in self:
            s.wsdrf_reported = s.wsdrf_expenses_available - s.wsdrf_expenses

    @api.depends('wsdrf_amount_before_expenses', 'wsdrf_expenses')
    def _compute_wsdrf_contribution(self):
        for s in self:
            s.wsdrf_contribution = (
                s.wsdrf_amount_before_expenses - s.wsdrf_expenses)

    @api.depends(
        'sub_total_payable', 'hsf_amount_payable',
        'cnt_amount_payable', 'wsdrf_contribution')
    def _compute_total_balance(self):
        for s in self:
            s.total_balance = (
                s.sub_total_payable + s.hsf_amount_payable +
                s.cnt_amount_payable + s.wsdrf_contribution)

            s.total_receivable = s.total_balance < 0 and -s.total_balance or 0
            s.total_payable = s.total_balance > 0 and s.total_balance or 0

    releve_1_ids = fields.One2many(
        'hr.releve_1', 'summary_id', 'Relevés 1',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    total_ids = fields.One2many(
        'hr.releve_1.summary.total', 'summary_id', 'Totals',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    qpp_amount_ee = fields.Float(
        'Source Deduction', required=True,
        help="Relevés 1 (box B)",
        **FLOAT_PARAM
    )
    qpp_amount_er = fields.Float(
        'Employer Contributions', required=True,
        **FLOAT_PARAM
    )
    qpp_amount_total = fields.Float(
        'Total Contribution',
        compute='_compute_qpp_amount_total',
        **FUNCTION_PARAM
    )

    qpip_amount_ee = fields.Float(
        'Source Deduction', required=True,
        help="Relevés 1 (box H)",
        **FLOAT_PARAM
    )
    qpip_amount_er = fields.Float(
        'Employer Contributions', required=True,
        **FLOAT_PARAM
    )
    qpip_amount_total = fields.Float(
        'Total Contribution',
        compute='_compute_qpip_amount_total',
        **FUNCTION_PARAM
    )

    qit_amount_1 = fields.Float(
        'Relevés 1 and 25', required=True,
        help="Relevés 1 (box E) et relevés 25 (box I)",
        **FLOAT_PARAM
    )
    qit_amount_2 = fields.Float(
        'Relevés 2',
        help="Relevés 2 (box J)",
        **FLOAT_PARAM
    )
    qit_amount_total = fields.Float(
        'Total Contribution',
        compute='_compute_qit_amount_total',
        **FUNCTION_PARAM
    )

    sub_total_contribution = fields.Float(
        'Sub Total',
        compute='_compute_sub_total_contribution',
        **FUNCTION_PARAM
    )

    sub_total_remitted = fields.Float(
        'Contributions Remitted', required=True,
        help="Source deductions and employer contributions "
        "remitted over the year for the QPP, QPIP "
        "and Quebec income tax (with forms TPZ-1015.R.14).",
        **FLOAT_PARAM
    )
    sub_total_payable = fields.Float(
        'QPP, QPIP and Income Tax to Pay',
        compute='_compute_sub_total_payable',
        **FUNCTION_PARAM
    )

    hsf_total_wage_bill = fields.Float(
        'Total Wage Bill', required=True,
        help="Refer to guide RL-1.G",
        **FLOAT_PARAM
    )
    hsf_salaries = fields.Float(
        'Salaries Eligible', required=True,
        **FLOAT_PARAM
    )
    hsf_exemption_code = fields.Selection(
        [('06', '06 - Investment Project in Quebec')],
        'Exemption Code',
        help="Let blank if no exemption. Otherwise, refer to guide RL-1.G."
    )
    hsf_exemption_amount = fields.Float(
        'Amount Exempted',
        **FLOAT_PARAM
    )
    hsf_contribution_rate = fields.Float(
        'Contribution Rate', digits=(1, 2), required=True,
        default=0,
        help="Refer to guide RL-1.G.",
    )
    hsf_amount_before_reduction = fields.Float(
        'Contribution Before Reduction',
        compute='_compute_hsf_amount_before_reduction',
        **FUNCTION_PARAM
    )

    hsf_reduction_basis = fields.Float(
        'Amount Admissible for the Reduction',
        **FLOAT_PARAM
    )
    hsf_reduction_rate = fields.Float(
        'Reduction Rate',
        **FLOAT_PARAM
    )
    hsf_reduction_amount = fields.Float(
        'Reduction of the Contribution',
        compute='_compute_hsf_reduction_amount',
        **FUNCTION_PARAM
    )

    hsf_amount_remitted = fields.Float(
        'Contributions Remitted', required=True,
        help="The HSF contributions already remitted during "
        "the year.",
        **FLOAT_PARAM
    )
    hsf_amount_payable = fields.Float(
        'Contribution to Pay',
        compute='_compute_hsf_amount_payable',
        **FUNCTION_PARAM
    )

    cnt_salaries = fields.Float(
        'CNT - Salaries Eligible', required=True,
        **FLOAT_PARAM
    )
    cnt_rate = fields.Float(
        'Rate', digits=(1, 2), required=True,
        default=0,
    )
    cnt_amount_payable = fields.Float(
        'CNT - Contribution',
        compute='_compute_cnt_amount_payable',
        **FUNCTION_PARAM
    )

    wsdrf_salaries = fields.Float(
        'Salares Eligible', required=True,
        help="The eligible salaries under the wsdrf "
        "if greater than 1,000,000 $"
        "Otherwise, 0.",
        **FLOAT_PARAM
    )
    wsdrf_rate = fields.Float(
        'Rate', digits=(1, 2), required=True,
        default=0,
    )
    wsdrf_amount_before_expenses = fields.Float(
        'Amount Before Expenses',
        compute='_compute_wsdrf_amount_before_expenses',
        **FUNCTION_PARAM
    )

    wsdrf_previous_reported = fields.Float(
        'Previous Year Balance',
        help="The amount of expenses that were "
        "reported from previous years.",
        **FLOAT_PARAM
    )
    wsdrf_expenses_current = fields.Float(
        'Expenses Current Year', required=True,
        help="The amount of eligible training expenses that were "
        "engaged in the year of reference.",
        **FLOAT_PARAM
    )
    wsdrf_expenses_available = fields.Float(
        'Expenses Available',
        compute='_compute_wsdrf_expenses_available',
        **FUNCTION_PARAM
    )
    wsdrf_expenses = fields.Float(
        'Expenses Deduced', required=True,
        help="The amount of expenses "
        "used to reduce the contribution",
        **FLOAT_PARAM
    )
    wsdrf_reported = fields.Float(
        'Expenses Reported',
        compute='_compute_wsdrf_reported',
        help="The amount of expenses to be "
        "reported to further years.",
        **FLOAT_PARAM
    )

    wsdrf_contribution = fields.Float(
        'Contribution',
        compute='_compute_wsdrf_contribution',
        **FUNCTION_PARAM
    )

    total_balance = fields.Float(
        'Total Balance',
        compute='_compute_total_balance',
        **FUNCTION_PARAM
    )
    total_receivable = fields.Float(
        'Total Receivable',
        compute='_compute_total_balance',
        **FUNCTION_PARAM
    )
    total_payable = fields.Float(
        'Total Payable',
        compute='_compute_total_balance',
        **FUNCTION_PARAM
    )

    @api.multi
    @api.constrains('releve_1_ids')
    def _check_employees(self):
        """
        A summary can not have more than one Relevé 1 per employee
        """
        for summary in self:

            slips = summary.releve_1_ids
            employees = slips.mapped('employee_id')

            if len(employees) != len(slips):
                raise ValidationError(
                    "Error! You can only have one Relevé 1 per employee "
                    "in a summary")

        return True

    @api.multi
    @api.constrains(
        'wsdrf_salaries', 'wsdrf_previous_reported',
        'wsdrf_expenses_current', 'wsdrf_expenses',
    )
    def _check_wsdrf_amount_deduced(self):
        """
        A summary can not have more than one Relevé 1 per employee
        """
        for summary in self:

            if summary.wsdrf_contribution < 0:
                raise ValidationError(
                    "Error! You can not deduce more training expenses than "
                    "the amount of contribution. The balance must be reported "
                    "to the next year")

        return True

    @api.multi
    def generate_slips(self):
        self.ensure_one()

        payslips = self.get_payslips()
        employees = payslips.mapped('employee_id')
        slips = self.releve_1_ids

        for employee in employees:

            employee.check_personal_info()

            slip = next(
                (s for s in slips if s.employee_id == employee), None)

            if slip is None:
                slip = self.env['hr.releve_1'].create({
                    'summary_id': self.id,
                    'employee_id': employee.id,
                    'company_id': self.company_id.id,
                    'slip_type': self.slip_type,
                    'year': self.year,
                })

            if not slip.computed:
                slip.compute_amounts()

        self.compute_totals()

    @api.multi
    def _get_total(self, ref):
        """
        Get the summary total record given the reference of the summary box
        """
        self.ensure_one()

        box = self.env.ref('payroll_quebec.%s' % ref)
        return sum((a.amount for a in self.total_ids if a.box_id == box), 0.0)

    @api.multi
    def compute_totals(self):
        self.ensure_one()

        self.write({'total_ids': [(5, 0)]})

        slip_ids = self.releve_1_ids.ids

        # Get all types of releve 1 summary box
        boxes = self.env['hr.releve_1.summary.box'].search([])

        self.write({
            'total_ids': [(0, 0, {
                'amount': box.compute_amount(slip_ids),
                'box_id': box.id,
            }) for box in boxes]
        })

        qpp_amount_ee = self._get_total('summary_box_qpp_amount_ee')
        qpip_amount_ee = self._get_total('summary_box_qpip_amount_ee')
        qit_amount_1 = self._get_total('summary_box_qit_amount_1')
        qpp_amount_er = self._get_total('summary_box_qpp_amount_er')
        qpip_amount_er = self._get_total('summary_box_qpip_amount_er')

        sub_total_remitted = (
            qpp_amount_ee + qpip_amount_ee + qit_amount_1 +
            qpp_amount_er + qpip_amount_er)

        hsf_salaries = self._get_total('summary_box_hsf_salaries')
        hsf_amount_er = self._get_total('summary_box_hsf_amount_er')
        total_pay = self._get_total('summary_box_total_pay')

        cnt_salaries = self._get_total('summary_box_cnt_salaries')
        wsdrf_salaries = self._get_total('summary_box_wsdrf_salaries')

        self.write({
            'qpp_amount_ee': qpp_amount_ee,
            'qpip_amount_ee': qpip_amount_ee,
            'qit_amount_1': qit_amount_1,
            'qpp_amount_er': qpp_amount_er,
            'qpip_amount_er': qpip_amount_er,
            'sub_total_remitted': sub_total_remitted,

            'hsf_salaries': hsf_salaries,
            'hsf_amount_remitted': hsf_amount_er,
            'hsf_total_wage_bill': total_pay,

            'cnt_salaries': cnt_salaries,
            'wsdrf_salaries': wsdrf_salaries
            if wsdrf_salaries >= 10 ** 7 else 0,
        })

    @api.multi
    def button_cancel(self):
        for summary in self:
            for slip in summary.releve_1_ids:
                slip.write({'state': 'cancelled'})
        self.write({'state': 'cancelled'})

    @api.multi
    def button_confirm_slips(self):
        for summary in self:
            slips = summary.releve_1_ids.filtered(lambda s: s.state == 'draft')
            slips.write({'state': 'confirmed'})

    @api.multi
    def button_confirm(self):
        for summary in self:
            for slip in summary.releve_1_ids:
                if slip.state in ['draft', 'cancelled']:
                    raise ValidationError(
                        _("Error"),
                        _("Every Relevé 1 must be confirmed before sending "
                          "the summary. Slip for employee %s is not "
                          "confirmed.") % slip.employee_id.name)

        self.write({'state': 'sent'})
        self.mapped('releve_1_ids').write({'state': 'sent'})
