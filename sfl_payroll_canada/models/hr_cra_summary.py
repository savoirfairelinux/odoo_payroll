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

import iso3166
import time

from collections import OrderedDict
from lxml import etree

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _


def dict_to_etree(element, d):
    """Populate an etree with the given dictionary"""
    for k, v in d.iteritems():
        if type(v) in [dict, OrderedDict]:
            child = etree.Element(k)
            dict_to_etree(child, v)
            element.append(child)
        elif type(v) is list:
            for item in v:
                child = etree.Element(k)
                element.append(child)
                dict_to_etree(child, item)
        else:
            child = etree.Element(k)
            element.append(child)
            child.text = unicode(v)


# Use functions to get the selection items, because otherwise, we get to
# translate the fields for every inheriting classes
def get_type_codes(self, cr, uid, context=None):
    return [
        ('O', _('Send Original Slips')),
        ('A', _('Send Amended Slips')),
        ('C', _('Cancel slips already sent')),
    ]


def get_language_codes(self, cr, uid, context=None):
    return [
        ('E', _('English')),
        ('F', _('French')),
    ]


def get_states(self, cr, uid, context=None):
    return [
        ('cancelled', _('Cancelled')),
        ('draft', _('Draft')),
        ('sent', _('Sent')),
    ]


class HrCraSummary(orm.AbstractModel):
    _name = 'hr.cra.summary'
    _description = 'CRA Summary'

    def make_address_dict(self, cr, uid, address, context=None):
        """
        Create a dict to be parsed into XML when generating fiscal slips
        of Canada Revenu Agency such as T4 and T619.

        @param address: A res.partner or hr.company browse record
        """
        for field in [
            ('street', _('Street Line 1')),
            ('city', _('City')),
            ('state_id', _('Province')),
            ('country_id', _('Country')),
            ('zip', _('Postal Code')),
        ]:
            if not address[field[0]]:
                raise orm.except_orm(
                    _('Error'),
                    _('The field %s for %s is missing')
                    % (field[1], address.name)
                )

        # Country code is in iso-3166-2, we need iso-3166-3
        country_code = address.country_id.code
        country = iso3166.countries.get(country_code)
        country_code = country.alpha3

        return {
            'addr_l1_txt': address.street[0:30],
            'addr_l2_txt': address.street2 and address.street2[0:30] or '',
            'cty_nm': address.city[0:28],
            'prov_cd': address.state_id.code,
            'cntry_cd': country_code,
            'pstl_cd': address.zip.replace(' ', ''),
        }

    def make_t619_xml(self, cr, uid, slip_return_xml, summary, context=None):
        """
        Summary XML of fiscal slips to the Canada Revenu Agency
        requires a section containing the T619.

        It Contains information about the transmitter and the standard
        header for all types of summarys.

        @param summary: The XML summary browse record
        @param slip_return_xml: The XML that contains the fiscal slips data
        """
        # Here, we suppose the company is the transmitter
        transmitter = summary.company_id

        # The working address of the transmitter
        transmitter_address_dict = self.make_address_dict(
            cr, uid, transmitter, context=context
        )

        contact_dict = {
            'cntc_nm': summary.contact_id.name[0:22],
            'cntc_area_cd': summary.contact_area_code,
            'cntc_phn_nbr': summary.contact_phone,
            'cntc_email_area': summary.contact_email,
        }
        if summary.contact_extension:
            contact_dict['cntc_extn_nbr'] = \
                summary.contact_extension

        name_dict = {
            'l1_nm': transmitter.name[0:30],
        }
        if len(transmitter.name) > 30:
            name_dict['l2_nm'] = transmitter.name[30:60]

        t619_dict = {
            'sbmt_ref_id': summary.sbmt_ref_id,
            'rpt_tcd': summary.type,
            'trnmtr_nbr': summary.trnmtr_nbr,
            'trnmtr_tcd': 3,
            'summ_cnt': summary.number_of_slips,
            'lang_cd': summary.lang_cd,
            'TRNMTR_NM': name_dict,
            'TRNMTR_ADDR': transmitter_address_dict,
            'CNTC': contact_dict,
        }

        t619 = etree.Element('T619')
        dict_to_etree(t619, t619_dict)
        t619_xml = etree.tostring(t619, pretty_print=True, encoding=unicode)

        return u"""<?xml version="1.0" encoding="UTF-8"?>
<Submission xmlns:ccms="http://www.cra-arc.gc.ca/xmlns/ccms/1-0-0"
xmlns:sdt="http://www.cra-arc.gc.ca/xmlns/sdt/2-2-0"
xmlns:ols="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols/1-0-1"
xmlns:ols1="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols1/1-0-1"
xmlns:ols10="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols10/1-0-1"
xmlns:ols100="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols100/1-0-1"
xmlns:ols12="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols12/1-0-1"
xmlns:ols125="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols125/1-0-1"
xmlns:ols140="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols140/1-0-1"
xmlns:ols141="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols141/1-0-1"
xmlns:ols2="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols2/1-0-1"
xmlns:ols5="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols5/1-0-1"
xmlns:ols50="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols50/1-0-1"
xmlns:ols52="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols52/1-0-1"
xmlns:ols6="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols6/1-0-1"
xmlns:ols8="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols8/1-0-1"
xmlns:ols9="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/ols9/1-0-1"
xmlns:olsbr="http://www.cra-arc.gc.ca/enov/ol/interfaces/efile/\
partnership/olsbr/1-0-1"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:noNamespaceSchemaLocation="layout-topologie.xsd">
%s
%s</Submission>""" % (t619_xml, slip_return_xml)

    _columns = {
        'xml': fields.text(
            'XML Generated', readonly=True,
        ),
        # This field is intended be inherited in other modules as a functional
        # field. It is used in method make_t619_xml.
        'number_of_slips': fields.integer(
            'Number of Slips', readonly=True,
        ),
        'sbmt_ref_id': fields.char(
            'Submission Reference', required=True, size=8,
            help="Number created by the company to identify the "
            "summary. It should contain 6 numeric characters",
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'trnmtr_nbr': fields.char(
            'Transmitter Number', required=True, size=8,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'lang_cd': fields.selection(
            get_language_codes,
            'Language of Communication',
            required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'state': fields.selection(
            get_states,
            'Status',
            select=True,
            readonly=True,
        ),
        'year': fields.integer(
            'Fiscal Year', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'type': fields.selection(
            get_type_codes,
            'Summary Type', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'contact_id': fields.many2one(
            'hr.employee', 'Contact', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'contact_area_code': fields.integer(
            'Contact Area Code', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'contact_phone': fields.char(
            'Contact Phone', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'contact_extension': fields.integer(
            'Contact Extension',
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'contact_email': fields.char(
            'Contact Email', size=60, required=True,
            readonly=True, states={'draft': [('readonly', False)]},
        ),

        'proprietor_1_id': fields.many2one(
            'hr.employee', 'Proprietor', required=True,
            help="The company's proprietor",
            readonly=True, states={'draft': [('readonly', False)]},
        ),
        'proprietor_2_id': fields.many2one(
            'hr.employee', 'Second Proprietor',
            readonly=True, states={'draft': [('readonly', False)]},
        ),
    }

    def _get_default_contact(self, cr, uid, context):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        if user.employee_ids:
            return user.employee_ids[0].id

        return False

    _defaults = {
        'state': 'draft',
        'lang_cd': 'E',
        'trnmtr_nbr': 'MM555555',
        'type': 'O',
        'company_id': lambda self, cr, uid, context:
        self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id,
        'year': lambda *a: int(time.strftime(
            DEFAULT_SERVER_DATE_FORMAT)[0:4]) - 1,
        'contact_id': _get_default_contact,
    }

    def _check_contact_phone(self, cr, uid, ids, context=None):
        """
        Check that the given contact phone number has the format 888-8888
        and that the area code is a 3 digits number
        """
        for summary in self.browse(cr, uid, ids, context=context):
            phone = summary.contact_phone
            phone = phone.split('-')
            if(
                len(phone) != 2 or
                len(phone[0]) != 3 or
                len(phone[1]) != 4 or
                not phone[0].isdigit() or
                not phone[1].isdigit()
            ):
                return False

            area_code = summary.contact_area_code
            if len(str(area_code)) != 3:
                return False

        return True

    _constraints = [
        (
            _check_contact_phone,
            "Error! The contact phone number must be in "
            "the following format: 123-1234 and the area code must "
            "have 3 digits",
            ['contact_area_code', 'contact_phone']
        ),
    ]

    def onchange_contact_id(
        self, cr, uid, ids, contact_id, context=None
    ):
        """
        Fill the contact's email address, phone and regional code
        """
        res = {'value': {}}
        if contact_id:
            contact = self.pool['hr.employee'].browse(
                cr, uid, contact_id, context=context)

            if contact.work_email:
                res['value']['contact_email'] = contact.work_email

            if contact.work_phone:
                phone = ''.join(
                    c for c in contact.work_phone
                    if c.isdigit())

                if len(phone) == 7:
                    phone = ''.join([phone[0:3], phone[3:]])

                elif len(phone) == 10:
                    res['value']['contact_area_code'] = int(phone[0:3])
                    phone = ''.join([phone[3:6], phone[6:]])

                res['value']['contact_phone'] = '-'.join([
                    phone[0:3], phone[3:7]])

        return res
