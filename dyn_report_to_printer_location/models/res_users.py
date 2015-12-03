# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.modules.registry import RegistryManager
from openerp.tools import SUPERUSER_ID
from .printing import _available_action_types


class ResUsers(models.Model):
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
        'Reset work location upon login',
        help=('Reset work location upon login, and prevent printing of any '
              'documents until the work location is reconfigured for the '
              'current session'))

    @api.multi
    def write(self, values):
        if values.get('work_location_id'):
            self.search(
                [('work_location_id', '=', values.get('work_location_id'))]
            ).sudo().write({'work_location_id': False})
        return super(ResUsers, self).write(values)

    _sql_constraints = [
        ('work_location_id_uniq', 'unique(work_location_id)',
         'Work Location must be unique!'),
    ]

    def _login(self, db, login, password):
        user_id = super(ResUsers, self)._login(db, login, password)
        if user_id:
            registry = RegistryManager.get(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                user = env['res.users'].browse(user_id)
                if user.reset_work_location:
                    user.write({'work_location_id': False})
        return user_id
