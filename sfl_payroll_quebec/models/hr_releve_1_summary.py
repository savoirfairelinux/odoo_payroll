# -*- coding:utf-8 -*-#########################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
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

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


# Use dicts of parameters to avoid redundance and errors
FUNCTION_PARAM = {
    'readonly': True,
    'states': {'draft': [('readonly', False)]},
    'method': True,
    'multi': True,
}


FLOAT_PARAM = {
    'readonly': True,
    'states': {'draft': [('readonly', False)]},
    'digits_compute': dp.get_precision('Payroll'),
}


class HrReleve1Summary(orm.Model):
    _name = 'hr.releve_1.summary'
    _description = 'Relevé 1 Summary'

    _inherit = 'hr.qc.summary'

    def _get_payslip_ids(self, cr, uid, ids, browse=False, context=None):
        summary = self.browse(cr, uid, ids[0], context=context)

        structure_id = self.pool['ir.model.data'].get_object_reference(
            cr, uid, 'sfl_payroll_quebec', 'hr_structure_qc')[1]

        structures = self.pool['hr.payroll.structure'].\
            get_children_recursively(
                cr, uid, [structure_id], context=context)

        date_from = datetime(summary.year, 1, 1).strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime(summary.year, 12, 31).strftime(
            DEFAULT_SERVER_DATE_FORMAT)

        payslip_obj = self.pool['hr.payslip']
        payslip_ids = payslip_obj.search(cr, uid, [
            ('date_payment', '>=', date_from),
            ('date_payment', '<=', date_to),
            ('company_id', '=', summary.company_id.id),
            ('struct_id', 'in', structures.ids),
            ('state', '=', 'done'),
        ], context=context)

        if not browse:
            return payslip_ids

        return payslip_obj.browse(cr, uid, payslip_ids, context=context)

    def _compute_amounts(
        self, cr, uid, ids, field_names, args=None, context=None
    ):
        res = {}

        for summary in self.browse(cr, uid, ids, context=context):

            qpp_amount_total = summary.qpp_amount_ee + summary.qpp_amount_er
            qpip_amount_total = summary.qpip_amount_ee + summary.qpip_amount_er
            qit_amount_total = summary.qit_amount_1 + summary.qit_amount_2

            sub_total_contribution = (
                qpp_amount_total + qpip_amount_total + qit_amount_total)

            sub_total_payable = sub_total_contribution - \
                summary.sub_total_remitted

            hsf_amount_before_reduction = (
                summary.hsf_salaries - summary.hsf_exemption_amount
            ) * summary.hsf_contribution_rate / 100

            hsf_reduction_amount = (
                summary.hsf_reduction_basis * summary.hsf_reduction_rate / 100)

            hsf_amount_payable = (
                hsf_amount_before_reduction - hsf_reduction_amount -
                summary.hsf_amount_remitted)

            cnt_amount_payable = (
                summary.cnt_salaries * summary.cnt_rate / 100)

            wsdrf_amount_before_expenses = (
                summary.wsdrf_salaries * summary.wsdrf_rate / 100)

            wsdrf_expenses_available = (
                summary.wsdrf_previous_reported +
                summary.wsdrf_expenses_current)

            wsdrf_reported = wsdrf_expenses_available - summary.wsdrf_expenses

            wsdrf_contribution = (
                wsdrf_amount_before_expenses - summary.wsdrf_expenses)

            total_balance = (
                sub_total_payable + hsf_amount_payable +
                cnt_amount_payable + wsdrf_contribution)

            total_receivable = total_balance < 0 and -total_balance or 0
            total_payable = total_balance > 0 and total_balance or 0

            res[summary.id] = {
                'qpp_amount_total': qpp_amount_total,
                'qpip_amount_total': qpip_amount_total,
                'qit_amount_total': qit_amount_total,
                'sub_total_contribution': sub_total_contribution,
                'sub_total_payable': sub_total_payable,
                'hsf_amount_before_reduction': hsf_amount_before_reduction,
                'hsf_reduction_amount': hsf_reduction_amount,
                'hsf_amount_payable': hsf_amount_payable,
                'cnt_amount_payable': cnt_amount_payable,
                'wsdrf_amount_before_expenses': wsdrf_amount_before_expenses,
                'wsdrf_expenses_available': wsdrf_expenses_available,
                'wsdrf_reported': wsdrf_reported,
                'wsdrf_contribution': wsdrf_contribution,
                'total_balance': total_balance,
                'total_receivable': total_receivable,
                'total_payable': total_payable,
            }

        return res

    _columns = {
        'releve_1_ids': fields.one2many(
            'hr.releve_1', 'summary_id', string='Relevés 1',
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'total_ids': fields.one2many(
            'hr.releve_1.summary.total',
            'summary_id',
            'Totals',
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'qpp_amount_ee': fields.float(
            'Source Deduction', required=True,
            help="Relevés 1 (box B)",
            **FLOAT_PARAM
        ),
        'qpp_amount_er': fields.float(
            'Employer Contributions', required=True,
            **FLOAT_PARAM
        ),
        'qpp_amount_total': fields.function(
            _compute_amounts,
            string='Total Contribution',
            **FUNCTION_PARAM
        ),

        'qpip_amount_ee': fields.float(
            'Source Deduction', required=True,
            help="Relevés 1 (box H)",
            **FLOAT_PARAM
        ),
        'qpip_amount_er': fields.float(
            'Employer Contributions', required=True,
            **FLOAT_PARAM
        ),
        'qpip_amount_total': fields.function(
            _compute_amounts,
            string='Total Contribution',
            **FUNCTION_PARAM
        ),

        'qit_amount_1': fields.float(
            'Relevés 1 and 25', required=True,
            help="Relevés 1 (box E) et relevés 25 (box I)",
            **FLOAT_PARAM
        ),
        'qit_amount_2': fields.float(
            'Relevés 2',
            help="Relevés 2 (box J)",
            **FLOAT_PARAM
        ),
        'qit_amount_total': fields.function(
            _compute_amounts,
            string='Total Contribution',
            **FUNCTION_PARAM
        ),

        'sub_total_contribution': fields.function(
            _compute_amounts,
            string='Sub Total',
            **FUNCTION_PARAM
        ),

        'sub_total_remitted': fields.float(
            'Contributions Remitted', required=True,
            help="Source deductions and employer contributions "
            "remitted over the year for the QPP, QPIP "
            "and Quebec income tax (with forms TPZ-1015.R.14).",
            **FLOAT_PARAM
        ),
        'sub_total_payable': fields.function(
            _compute_amounts,
            string='QPP, QPIP and Income Tax to Pay',
            **FUNCTION_PARAM
        ),

        'hsf_total_wage_bill': fields.float(
            'Total Wage Bill', required=True,
            help="Refer to guide RL-1.G",
            **FLOAT_PARAM
        ),
        'hsf_salaries': fields.float(
            'Salaries Eligible', required=True,
            **FLOAT_PARAM
        ),
        'hsf_exemption_code': fields.selection(
            [('06', '06 - Investment Project in Quebec')],
            string='Exemption Code',
            help="Let blank if no exemption. Otherwise, refer to guide RL-1.G."
        ),
        'hsf_exemption_amount': fields.float(
            'Amount Exempted',
            **FLOAT_PARAM
        ),
        'hsf_contribution_rate': fields.float(
            'Contribution Rate', digits=(1, 2), required=True,
            help="Refer to guide RL-1.G.",
        ),
        'hsf_amount_before_reduction': fields.function(
            _compute_amounts,
            string='Contribution Before Reduction',
            **FUNCTION_PARAM
        ),

        'hsf_reduction_basis': fields.float(
            'Amount Admissible for the Reduction',
            **FLOAT_PARAM
        ),
        'hsf_reduction_rate': fields.float(
            'Reduction Rate',
            **FLOAT_PARAM
        ),
        'hsf_reduction_amount': fields.function(
            _compute_amounts,
            string='Reduction of the Contribution',
            **FUNCTION_PARAM
        ),

        'hsf_amount_remitted': fields.float(
            'Contributions Remitted', required=True,
            help="The HSF contributions already remitted during "
            "the year.",
            **FLOAT_PARAM
        ),
        'hsf_amount_payable': fields.function(
            _compute_amounts,
            string='Contribution to Pay',
            **FUNCTION_PARAM
        ),

        'cnt_salaries': fields.float(
            'CNT - Salaries Eligible', required=True,
            **FLOAT_PARAM
        ),
        'cnt_rate': fields.float(
            'Rate', digits=(1, 2), required=True, readonly=True,
        ),
        'cnt_amount_payable': fields.function(
            _compute_amounts,
            string='CNT - Contribution',
            **FUNCTION_PARAM
        ),

        'wsdrf_salaries': fields.float(
            'Salares Eligible', required=True,
            help="The eligible salaries under the wsdrf "
            "if greater than 1,000,000 $"
            "Otherwise, 0.",
            **FLOAT_PARAM
        ),
        'wsdrf_rate': fields.float(
            'Rate', digits=(1, 2), required=True, readonly=True,
        ),
        'wsdrf_amount_before_expenses': fields.function(
            _compute_amounts,
            string='Amount Before Expenses',
            **FUNCTION_PARAM
        ),

        'wsdrf_previous_reported': fields.float(
            'Previous Year Balance',
            help="The amount of expenses that were "
            "reported from previous years.",
            **FLOAT_PARAM
        ),
        'wsdrf_expenses_current': fields.float(
            'Expenses Current Year', required=True,
            help="The amount of eligible training expenses that were "
            "engaged in the year of reference.",
            **FLOAT_PARAM
        ),
        'wsdrf_expenses_available': fields.function(
            _compute_amounts,
            string='Expenses Available',
            **FUNCTION_PARAM
        ),
        'wsdrf_expenses': fields.float(
            'Expenses Deduced', required=True,
            help="The amount of expenses "
            "used to reduce the contribution",
            **FLOAT_PARAM
        ),
        'wsdrf_reported': fields.function(
            _compute_amounts,
            string='Expenses Reported',
            help="The amount of expenses to be "
            "reported to further years.",
            **FUNCTION_PARAM
        ),

        'wsdrf_contribution': fields.function(
            _compute_amounts,
            string='Contribution',
            **FUNCTION_PARAM
        ),

        'total_balance': fields.function(
            _compute_amounts,
            string='Total Balance',
            **FUNCTION_PARAM
        ),
        'total_receivable': fields.function(
            _compute_amounts,
            string='Total Receivable',
            **FUNCTION_PARAM
        ),
        'total_payable': fields.function(
            _compute_amounts,
            string='Total Payable',
            **FUNCTION_PARAM
        ),
    }

    def _check_employees(self, cr, uid, ids, context=None):
        """
        A summary can not have more than one Relevé 1 per employee
        """
        for summary in self.browse(cr, uid, ids, context=context):

            slips = summary.releve_1_ids

            employee_ids = {
                slip.employee_id.id for slip in slips
            }

            if not len(employee_ids) == len(slips):
                return False

        return True

    def _check_wsdrf_amount_deduced(self, cr, uid, ids, context=None):
        """
        A summary can not have more than one Relevé 1 per employee
        """
        for summary in self.browse(cr, uid, ids, context=context):

            if summary.wsdrf_contribution < 0:
                return False

        return True

    _constraints = [
        (
            _check_employees,
            "Error! You can only have one Relevé 1 per employee "
            "in a summary",
            ['releve_1_ids']
        ),
        (
            _check_wsdrf_amount_deduced,
            "Error! You can not deduce more training expenses than "
            "the amount of contribution. The balance must be reported "
            "to the next year",
            [
                'wsdrf_salaries', 'wsdrf_previous_reported',
                'wsdrf_expenses_current', 'wsdrf_expenses',
            ]
        ),
    ]

    _defaults = {
        'cnt_rate': 0.08,
        'wsdrf_rate': 1.0,
        'qpp_amount_ee': 0.0,
        'qpp_amount_er': 0.0,
        'qpip_amount_ee': 0.0,
        'qpip_amount_er': 0.0,
        'qit_amount_1': 0.0,
        'sub_total_remitted': 0.0,
        'hsf_total_wage_bill': 0.0,
        'hsf_salaries': 0.0,
        'hsf_contribution_rate': 0.0,
        'hsf_amount_remitted': 0.0,
        'cnt_salaries': 0.0,
        'wsdrf_salaries': 0.0,
        'wsdrf_expenses_current': 0.0,
        'wsdrf_expenses': 0.0,
    }

    def generate_slips(self, cr, uid, ids, context=None):
        summary = self.browse(cr, uid, ids[0], context=context)

        payslips = summary._get_payslip_ids(browse=True)

        employees = {payslip.employee_id for payslip in payslips}

        slips = summary.releve_1_ids
        slip_obj = self.pool['hr.releve_1']

        for employee in employees:

            employee.check_personal_info()

            slip = next(
                (s for s in slips if s.employee_id == employee), False)

            if not slip:
                slip_id = slip_obj.create(cr, uid, {
                    'employee_id': employee.id,
                    'company_id': summary.company_id.id,
                    'slip_type': summary.slip_type,
                    'year': summary.year,
                }, context=context)

                summary.write({'releve_1_ids': [(4, slip_id)]})

                slip = slip_obj.browse(cr, uid, slip_id, context=context)

            if not slip.computed:
                slip.compute_amounts()

        summary.compute_totals()

    def _get_total(self, cr, uid, ids, ref_list, context=None):
        """
        Get the summary total record given the reference of the summary box

        :param ref_list: list of xml reference of summary boxes
        or single reference
        """
        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1

        summary = self.browse(cr, uid, ids[0], context=context)

        box_id = self.pool['ir.model.data'].get_object_reference(
            cr, uid, 'sfl_payroll_quebec', ref_list)[1]

        box = self.pool['hr.releve_1.summary.box'].browse(
            cr, uid, box_id, context=context)

        return sum(
            (a.amount for a in summary.total_ids if a.box_id == box), 0.0)

    def compute_totals(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1

        summary = self.browse(cr, uid, ids[0], context=context)

        summary.write({'total_ids': [(5, 0)]})

        slip_ids = [s.id for s in summary.releve_1_ids]

        box_obj = self.pool['hr.releve_1.summary.box']

        # Get all types of releve 1 summary box
        box_ids = box_obj.search(cr, uid, [], context=context)
        boxes = box_obj.browse(cr, uid, box_ids, context=context)

        summary.write({
            'total_ids': [(0, 0, {
                'amount': box.compute_amount(slip_ids),
                'box_id': box.id,
            }) for box in boxes]
        })

        qpp_amount_ee = summary._get_total('summary_box_qpp_amount_ee')
        qpip_amount_ee = summary._get_total('summary_box_qpip_amount_ee')
        qit_amount_1 = summary._get_total('summary_box_qit_amount_1')
        qpp_amount_er = summary._get_total('summary_box_qpp_amount_er')
        qpip_amount_er = summary._get_total('summary_box_qpip_amount_er')

        sub_total_remitted = (
            qpp_amount_ee + qpip_amount_ee + qit_amount_1 +
            qpp_amount_er + qpip_amount_er)

        hsf_salaries = summary._get_total('summary_box_hsf_salaries')
        hsf_amount_er = summary._get_total('summary_box_hsf_amount_er')
        total_pay = summary._get_total('summary_box_total_pay')

        cnt_salaries = summary._get_total('summary_box_cnt_salaries')
        wsdrf_salaries = summary._get_total('summary_box_wsdrf_salaries')

        summary.write({
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

    def button_cancel(self, cr, uid, ids, context=None):
        for summary in self.browse(cr, uid, ids, context=context):
            for slip in summary.releve_1_ids:
                slip.write({'state': 'cancelled'})
            summary.write({'state': 'cancelled'})

    def button_confirm_slips(self, cr, uid, ids, context=None):
        summary = self.browse(cr, uid, ids[0], context=context)

        slip_ids = [
            slip.id for slip in summary.releve_1_ids
            if slip.state == 'draft'
        ]

        self.pool['hr.releve_1'].write(cr, uid, slip_ids, {
            'state': 'confirmed'}, context=context)

    def button_confirm(self, cr, uid, ids, context=None):
        summary = self.browse(cr, uid, ids[0], context=context)
        summary.write({'state': 'sent'})

        for slip in summary.releve_1_ids:
            if slip.state in ['draft', 'cancelled']:
                raise orm.except_orm(
                    _("Error"),
                    _("Every Relevé 1 must be confirmed before sending the "
                        "summary. Slip for employee %s is not confirmed.") %
                    slip.employee_id.name
                )

        slip_ids = [slip.id for slip in summary.releve_1_ids]

        self.pool['hr.releve_1'].write(cr, uid, slip_ids, {
            'state': 'sent'}, context=context)
