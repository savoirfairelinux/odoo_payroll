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

from openerp import models, fields, api, exceptions, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.one
    @api.depends('contract_job_ids')
    def _get_main_job_position(self):
        """
        Get the main job position from the field contract_job_ids which
        contains one and only one record with field is_main_job == True
        """
        main_job = self.contract_job_ids.filtered('is_main_job') or False
        if main_job:
            main_job = main_job[0].job_id.id
        self.job_id = main_job

    contract_job_ids = fields.One2many(
        'hr.contract.job',
        'contract_id',
        string='Jobs',
    )

    # Modify the job_id field so that it points to the main job
    job_id = fields.Many2one(
        'hr.job',
        string="Job Title",
        compute="_get_main_job_position",
        store=True,
    )

    @api.multi
    @api.constrains('contract_job_ids')
    def _check_one_main_job(self):
        if self.env.context.get('defer_constrains'):
            return

        for contract in self:
            # if the contract has no job assigned, a main job
            # is not required. Otherwise, one main job assigned is
            # required.
            if contract.contract_job_ids:
                main_jobs = contract.contract_job_ids.filtered('is_main_job')
                if len(main_jobs) != 1:
                    raise exceptions.Warning(
                        _("You must assign one and only one job position "
                          "as main job position."))

    @api.multi
    def write(self, vals):
        if vals.get('job_id') and not vals.get('contract_job_ids'):
            self.set_main_job(vals.get('job_id'))
        return super(HrContract, self).write(vals)

    @api.one
    def add_job(self, job_id, main_job):
        self.write({
            'contract_job_ids': [
                (0, 0, {
                    'is_main_job': main_job,
                    'job_id': job_id,
                }),
            ]
        })

    @api.one
    def set_main_job(self, job_id):
        assert isinstance(job_id, (int, long)), 'Expected Integer'

        job = self.env['hr.job'].browse(job_id)
        contract_job = self.contract_job_ids.filtered(
            lambda j: j.job_id == job)

        ctx = {'defer_constrains': True}

        if contract_job:
            contract_job[0].with_context(ctx).write({
                'is_main_job': True,
            })
        else:
            self.with_context(ctx).add_job(job_id, main_job=True)

        self.refresh()
        self.contract_job_ids.filtered(
            lambda j: j.job_id != job).write({'is_main_job': False})
