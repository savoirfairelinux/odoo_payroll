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

from collections import OrderedDict
from lxml import etree

from openerp.osv import fields, orm
from openerp.tools.translate import _

from .hr_cra_summary import dict_to_etree


class HrCraT4Summary(orm.Model):
    _name = 'hr.cra.t4.summary'
    _inherit = 'hr.cra.summary'
    _description = 'T4 Summary'

    def button_confirm(self, cr, uid, ids, context=None):
        summary = self.browse(cr, uid, ids[0], context=context)
        summary.write({'state': 'sent'})

        slips = summary.t4_slip_ids

        for slip in slips:
            if slip.state in ['draft', 'cancelled']:
                raise orm.except_orm(
                    _("Error"),
                    _(
                        "Every T4 must be confirmed before sending the "
                        "summary. The slip for employee %s is not confirmed."
                    ) % slip.employee_id.name)

        for slip in slips:
            slip.write({'state': 'sent'})

        summary.generate_xml()

    def button_confirm_slips(self, cr, uid, ids, context=None):
        summary = self.browse(cr, uid, ids[0], context=context)

        slip_ids = [
            slip.id for slip in summary.t4_slip_ids
            if slip.state == 'draft'
        ]

        self.pool['hr.cra.t4'].write(cr, uid, slip_ids, {
            'state': 'confirmed'}, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        for summary in self.browse(cr, uid, ids, context=context):
            for slip in summary.t4_slip_ids:
                slip.write({'state': 'cancelled'})
            summary.write({'state': 'cancelled'})

    def _get_payslip_ids(self, cr, uid, ids, browse=False, context=None):
        summary = self.browse(cr, uid, ids[0], context=context)

        structure_id = self.pool['ir.model.data'].get_object_reference(
            cr, uid, 'sfl_payroll_canada', 'hr_structure_ca_base')[1]

        structure_ids = self.pool['hr.payroll.structure'].\
            get_children_recursively(
                cr, uid, [structure_id], context=context).ids

        payslip_obj = self.pool['hr.payslip']
        payslip_ids = payslip_obj.search(cr, uid, [
            ('date_payment', '>=', "%s-01-01" % summary.year),
            ('date_payment', '<=', "%s-12-31" % summary.year),
            ('company_id', '=', summary.company_id.id),
            ('struct_id', 'in', structure_ids),
            ('state', '=', 'done'),
        ], context=context)

        if not browse:
            return payslip_ids

        return payslip_obj.browse(cr, uid, payslip_ids, context=context)

    def generate_slips(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, "Expected single record"

        summary = self.browse(cr, uid, ids[0], context=context)

        payslips = summary._get_payslip_ids(browse=True)
        employees = {payslip.employee_id for payslip in payslips}

        slips = summary.t4_slip_ids
        slip_obj = self.pool['hr.cra.t4']

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
                slip_id = slip_obj.create(cr, uid, {
                    'employee_id': employee.id,
                    'company_id': summary.company_id.id,
                    'type': summary.type,
                    'year': summary.year,
                    'empt_prov_cd': empt_prov_cd,
                    'summary_id': summary.id,
                }, context=context)

                slip = slip_obj.browse(cr, uid, slip_id, context=context)

            if not slip.computed:
                slip.compute_amounts()

        summary.compute_totals()

    def generate_xml(
        self, cr, uid, ids, context=None
    ):
        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, "Expected single record"

        cra_summary_obj = self.pool['hr.cra.summary']

        summary = self.browse(cr, uid, ids[0], context=context)

        # We create an empty list of T4 slip dicts
        t4_slip_dict_list = []
        for t4_slip in summary.t4_slip_ids:

            employee = t4_slip.employee_id
            employee.check_personal_info()

            # T4 slip input amounts
            std_amounts = [
                a for a in t4_slip.amount_ids
                if not a.is_other_amount and
                a.box_id.appears_on_summary
            ]

            amounts_dict = {
                a.box_id.xml_tag: "%.2f" % a.amount
                for a in std_amounts
            }

            other_amounts = [
                a for a in t4_slip.amount_ids
                if a.is_other_amount and
                a.box_id.appears_on_summary
            ]

            # Identification of the employee
            name_dict = {
                'snm': employee.lastname[0:20],
                'gvn_nm': employee.firstname[0:12],
            }
            if employee.lastname_initial:
                name_dict['init'] = employee.lastname_initial

            address_dict = cra_summary_obj.make_address_dict(
                cr, uid, employee.address_home_id, context=context)

            t4_slip_dict = {
                'EMPE_NM': name_dict,
                'EMPE_ADDR': address_dict,
                'sin': int(employee.sin),
                'bn': summary.company_id.cra_payroll_number,

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
        company = summary.company_id

        # The company address
        company_address_dict = cra_summary_obj.make_address_dict(
            cr, uid, company, context=context
        )

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
        pprtr_sin = {'pprtr_1_sin': int(summary.proprietor_1_id.sin)}
        if summary.proprietor_2_id:
            pprtr_sin['pprtr_2_sin'] = int(summary.proprietor_2_id.sin)

        # Convert results to string
        amount_sum_dict = {
            total.box_id.xml_tag: "%.2f" % total.amount
            for total in summary.total_ids
        }

        # The contact is required
        # all fields are mandatory but the extension
        contact_dict = {
            'cntc_nm': summary.contact_id.name[0:22],
            'cntc_area_cd': summary.contact_area_code,
            'cntc_phn_nbr': summary.contact_phone,
        }
        if summary.contact_extension:
            contact_dict['cntc_extn_nbr'] = \
                summary.contact_extension

        t4_summary_dict = {
            'bn': summary.company_id.cra_payroll_number,
            'EMPR_ADDR': company_address_dict,
            'EMPR_NM': name_dict,
            'CNTC': contact_dict,
            'tx_yr': summary.year,
            'slp_cnt': len(summary.t4_slip_ids),
            'PPRTR_SIN': pprtr_sin,
            'rpt_tcd': summary.type,
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
            cr, uid, slip_return_xml, summary, context=context
        )

        # We write the resulting XML structure to the XML field
        summary.write({'xml': t619_xml})

    def _count_slips(
        self, cr, uid, ids, field_name, arg=None, context=None
    ):
        """ Count the T4 slips in summary """
        res = {}

        for summary in self.browse(cr, uid, ids, context=context):
            res[summary.id] = len(summary.t4_slip_ids)

        return res

    def compute_totals(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, "Expected single record"

        summary = self.browse(cr, uid, ids[0], context=context)

        summary.write({'total_ids': [(5, 0)]})

        slip_ids = [s.id for s in summary.t4_slip_ids]

        box_obj = self.pool['hr.cra.t4.summary.box']

        # Get all types of t4 summary box
        box_ids = box_obj.search(cr, uid, [], context=context)
        boxes = box_obj.browse(cr, uid, box_ids, context=context)

        summary.write({
            'total_ids': [(0, 0, {
                'amount': box.compute_amount(slip_ids),
                'box_id': box.id,
            }) for box in boxes]
        })

    _columns = {
        'name': fields.char('Name', required=True),
        't4_slip_ids': fields.one2many(
            'hr.cra.t4',
            'summary_id',
            string="T4 Slips",
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'number_of_slips': fields.function(
            _count_slips, type="integer",
            string="Number of Slips",
            readonly=True,
        ),
        'total_ids': fields.one2many(
            'hr.cra.t4.summary.total',
            'summary_id',
            'Totals',
            readonly=True, states={'draft': [('readonly', False)]},
        ),
    }

    _defaults = {
        'name': lambda self, cr, uid, c={}:
        self.pool['ir.sequence'].get(cr, uid, 'hr.cra.t4.summary'),
    }
