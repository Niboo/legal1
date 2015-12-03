# -*- coding: utf-8 -*-
from openerp import models, fields, api

from .printing import _available_action_types


class res_users(models.Model):
    _inherit = 'res.users'

    def _user_available_action_types_inherit(self):
        return [(code, string) for code, string
                in _available_action_types(self)
                if code != 'user_default']

    printing_action = fields.Selection(
        _user_available_action_types_inherit)
    work_location_id = fields.Many2one(
        'work_location', string='Work Location', required=False)
    reset_work_location = fields.Boolean(
        'Reset work location upon login', default=True)

    @api.multi
    def write(self, values):
        if values.get('work_location_id'):
            self.search(
                [('work_location_id', '=', values.get('work_location_id'))]
            ).sudo().write({'work_location_id': False})
        return super(res_users, self).write(values)

    _sql_constraints = [
        ('work_location_id_uniq', 'unique(work_location_id)',
         'Work Location must be unique!'),
    ]
