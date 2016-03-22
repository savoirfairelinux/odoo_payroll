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

from collections import OrderedDict
from lxml import etree

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError

from .hr_cra_summary import dict_to_etree


class HrCraT4Summary(models.Model):
    """T4 Summary"""

    _name = 'hr.cra.t4.summary'
    _inherit = 'hr.cra.summary'
    _description = _(__doc__)

    @api.multi
    def button_confirm(self):
        self.ensure_one()
        self.write({'state': 'sent'})

        for t4 in self.t4_slip_ids:
            if t4.state in ['draft', 'cancelled']:
                raise ValidationError(
                    _(
                        "Every T4 must be confirmed before sending the "
                        "summary. The slip for employee %s is not confirmed."
                    ) % t4.employee_id.name)

        self.t4_slip_ids.write({'state': 'sent'})

        self.generate_xml()

    @api.multi
    def button_confirm_slips(self):
        self.ensure_one()
        slips = self.t4_slip_ids.filtered(lambda t4: t4.state == 'draft')
        slips.write({'state': 'confirmed'})

    @api.multi
    def button_cancel(self):
        self.ensure_one()
        self.t4_slip_ids.write({'state': 'cancelled'})
        self.write({'state': 'cancelled'})

    @api.multi
    def get_payslips(self):
        self.ensure_one()

        structure = self.env.ref('payroll_canada.hr_structure_ca_base')
        structure_ids = structure.get_children_recursively().ids

        payslips = self.env['hr.payslip'].search([
            ('date_payment', '>=', "%s-01-01" % self.year),
            ('date_payment', '<=', "%s-12-31" % self.year),
            ('company_id', '=', self.company_id.id),
            ('struct_id', 'in', structure_ids),
            ('state', '=', 'done'),
        ])

        return payslips

    @api.multi
    def generate_slips(self):
        self.ensure_one()

        payslips = self.get_payslips()
        employees = payslips.mapped('employee_id')

        slips = self.t4_slip_ids
        slip_obj = self.env['hr.cra.t4']

        for employee in employees:
            employee.check_personal_info()

            slip = next(
                (s for s in slips if s.employee_id == employee), False)

            state = employee.address_id.state_id
            if state.country_id.code == 'CA':
                empt_prov_cd = state.code
            else:
                empt_prov_cd = 'ZZ'

            if not slip:
                slip = slip_obj.create({
                    'employee_id': employee.id,
                    'company_id': self.company_id.id,
                    'type': self.type,
                    'year': self.year,
                    'empt_prov_cd': empt_prov_cd,
                    'summary_id': self.id,
                })

            if not slip.computed:
                slip.compute_amounts()

        self.compute_totals()

    @api.multi
    def generate_xml(self):
        self.ensure_one()

        cra_summary_obj = self.env['hr.cra.summary']

        # We create an empty list of T4 slip dicts
        t4_slip_dict_list = []
        for t4_slip in self.t4_slip_ids:

            employee = t4_slip.employee_id
            employee.check_personal_info()

            # T4 slip input amounts
            std_amounts = t4_slip.amount_ids.filtered(
                lambda a: not a.is_other_amount and
                a.box_id.appears_on_summary
            )

            amounts_dict = {
                a.box_id.xml_tag: "%.2f" % a.amount
                for a in std_amounts
            }

            other_amounts = t4_slip.amount_ids.filtered(
                lambda a: a.is_other_amount and
                a.box_id.appears_on_summary
            )

            # Identification of the employee
            name_dict = {
                'snm': employee.lastname[0:20],
                'gvn_nm': employee.firstname[0:12],
            }
            if employee.lastname_initial:
                name_dict['init'] = employee.lastname_initial

            address_dict = cra_summary_obj.make_address_dict(
                employee.address_home_id)

            t4_slip_dict = {
                'EMPE_NM': name_dict,
                'EMPE_ADDR': address_dict,
                'sin': int(employee.sin),
                'bn': self.company_id.cra_payroll_number,

                # Boolean fields (we need 0 or 1)
                'cpp_qpp_xmpt_cd': int(t4_slip.cpp_qpp_xmpt_cd),
                'ei_xmpt_cd': int(t4_slip.ei_xmpt_cd),
                'prov_pip_xmpt_cd': int(t4_slip.prov_pip_xmpt_cd),

                'rpt_tcd': t4_slip.type,
                'empt_prov_cd': t4_slip.empt_prov_cd,
                'T4_AMT': amounts_dict,
                'OTH_INFO': {
                    a.box_id.xml_tag: "%0.2f" % a.amount
                    for a in other_amounts
                }
            }

            # Optional fields on T4 Slip
            if t4_slip.empt_cd:
                t4_slip_dict['empt_cd'] = t4_slip.empt_cd

            if t4_slip.rpp_dpsp_rgst_nbr:
                t4_slip_dict['rpp_dpsp_rgst_nbr'] = \
                    t4_slip.rpp_dpsp_rgst_nbr

            if employee.employee_number:
                t4_slip_dict['no_employee'] = employee.employee_number

            # Append the current T4 dict to the list of T4 dicts
            t4_slip_dict_list.append(t4_slip_dict)

        # Company
        company = self.company_id

        # The company address
        company_address_dict = cra_summary_obj.make_address_dict(
            company)

        company_name = company.name
        # The CRA wants '&' replaced by '&amp;' in company name
        # The problem is that they also want the name split into
        # 2 rows of 30 chars max. Not worth the time so we remove '&'.
        company_name.replace('&', '')
        name_dict = {
            'l1_nm': company_name[0:30],
        }
        if len(company_name) > 30:
            name_dict['l2_nm'] = company_name[30:60]

        # Social insurance numbers of proprietors
        pprtr_sin = {'pprtr_1_sin': int(self.proprietor_1_id.sin)}
        if self.proprietor_2_id:
            pprtr_sin['pprtr_2_sin'] = int(self.proprietor_2_id.sin)

        # Convert results to string
        amount_sum_dict = {
            total.box_id.xml_tag: "%.2f" % total.amount
            for total in self.total_ids
        }

        # The contact is required
        # all fields are mandatory but the extension
        contact_dict = {
            'cntc_nm': self.contact_id.name[0:22],
            'cntc_area_cd': self.contact_area_code,
            'cntc_phn_nbr': self.contact_phone,
        }
        if self.contact_extension:
            contact_dict['cntc_extn_nbr'] = \
                self.contact_extension

        t4_summary_dict = {
            'bn': self.company_id.cra_payroll_number,
            'EMPR_ADDR': company_address_dict,
            'EMPR_NM': name_dict,
            'CNTC': contact_dict,
            'tx_yr': self.year,
            'slp_cnt': len(self.t4_slip_ids),
            'PPRTR_SIN': pprtr_sin,
            'rpt_tcd': self.type,
            'T4_TAMT': amount_sum_dict,
        }

        slip_return_xml = etree.Element('Return')
        return_dict = OrderedDict()
        return_dict['T4Slip'] = t4_slip_dict_list
        return_dict['T4Summary'] = t4_summary_dict
        dict_to_etree(slip_return_xml, {'T4': return_dict})

        slip_return_xml = etree.tostring(
            slip_return_xml, pretty_print=True, encoding=unicode)

        # This function creates the T619 xml structure.
        # This structures embeds the slip return xml.
        # Seperated this in another file, because it is a
        # distinct structure.
        t619_xml = cra_summary_obj.make_t619_xml(
            slip_return_xml, self)

        # We write the resulting XML structure to the XML field
        self.write({'xml': t619_xml})

    @api.multi
    def _count_slips(self):
        for summary in self:
            summary.number_of_slips = len(summary.t4_slip_ids)

    @api.multi
    def compute_totals(self):
        self.ensure_one()

        self.write({'total_ids': [(5, 0)]})

        boxes = self.env['hr.cra.t4.summary.box'].search([])

        self.write({
            'total_ids': [(0, 0, {
                'amount': box.compute_amount(self.t4_slip_ids.ids),
                'box_id': box.id,
            }) for box in boxes]
        })

    name = fields.Char(
        'Name',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'hr.cra.t4.summary'),
    )
    t4_slip_ids = fields.One2many(
        'hr.cra.t4',
        'summary_id',
        string="T4 Slips",
        readonly=True, states={'draft': [('readonly', False)]},
    )
    number_of_slips = fields.Integer(
        "Number of Slips",
        compute='_count_slips',
        readonly=True,
    )
    total_ids = fields.One2many(
        'hr.cra.t4.summary.total',
        'summary_id',
        'Totals',
        readonly=True, states={'draft': [('readonly', False)]},
    )
