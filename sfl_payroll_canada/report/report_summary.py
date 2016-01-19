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

from openerp.report import report_sxw
from openerp.osv import orm
from openerp.tools.translate import _


class report_cra_summary(report_sxw.report_sxw):
    def create(self, cr, uid, ids, data, context=None):
        if not ids or len(ids) > 1:
            raise orm.except_orm(
                _("Error"),
                _("You must select one and only one summary"))

        summary = self.getObjects(cr, uid, ids, context)[0]

        if not summary.state == 'sent':
            raise orm.except_orm(
                _("Error"),
                _("The summary must be confirmed before generating the "
                    "XML for transmission."))

        return summary.xml, 'txt'


report_cra_summary(
    'report.t4_summary_xml',
    'hr.cra.t4.summary',
    parser=False,
    header=False
)
