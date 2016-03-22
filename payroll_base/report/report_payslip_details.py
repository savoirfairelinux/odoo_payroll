# -*- coding:utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2015 Savoif-faire Linux
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

from openerp.api import Environment
from openerp.osv import osv
from openerp.report import report_sxw


class PayslipDetailsReport(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(PayslipDetailsReport, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_details_by_rule_category': self.get_details_by_rule_category,
        })

        self.env = Environment(cr, uid, context)

    def get_details_by_rule_category(self, obj):
        payslip_line_obj = self.env['hr.payslip.line']
        rule_cate_obj = self.env['hr.salary.rule.category']

        res = []

        def get_recursive_parent(categories):
            res = categories
            parents = categories.mapped('parent_id')

            while(parents):
                grand_parents = parents.mapped('parent_id')
                res += parents
                parents = grand_parents

            return res

        if obj:

            payslip_line_rows = {}

            self.cr.execute(
                """SELECT pl.id, pl.category_id
                FROM hr_payslip_line as pl, hr_salary_rule_category as rc
                WHERE pl.category_id = rc.id AND pl.id in %s
                GROUP BY rc.parent_id, pl.sequence, pl.id, pl.category_id
                ORDER BY pl.sequence, rc.parent_id
                """, (tuple(obj.ids),))

            for x in self.cr.fetchall():
                payslip_line_rows.setdefault(x[1], [])
                payslip_line_rows[x[1]].append(x[0])

            for category_id, rule_ids in payslip_line_rows.iteritems():

                payslip_lines = payslip_line_obj.browse(rule_ids)
                category_total = sum(line.amount for line in payslip_lines)

                level = 0

                rule_category = rule_cate_obj.browse(category_id)
                parents = get_recursive_parent(rule_category)

                for parent in parents:
                    res.append({
                        'rule_category': parent.name,
                        'name': parent.name,
                        'code': parent.code,
                        'level': level,
                        'total': category_total,
                    })
                    level += 1

                for line in payslip_lines:
                    res.append({
                        'rule_category': line.name,
                        'name': line.name,
                        'code': line.code,
                        'total': line.amount,
                        'level': level
                    })

        return res


class WrappedReportPayslipDetails(osv.AbstractModel):
    _name = 'report.payroll_base.report_payslip_details'
    _inherit = 'report.abstract_report'
    _template = 'payroll_base.report_payslip_details'
    _wrapped_report_class = PayslipDetailsReport
