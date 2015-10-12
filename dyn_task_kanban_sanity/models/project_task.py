# -*- coding: utf-8 -*-
from openerp import fields, models


class project_task(models.Model):
    _inherit = 'project.task'

    stage_id = fields.Many2one('project.task.type', 'Stage', ondelete='restrict')
