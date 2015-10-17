# -*- coding: utf-8 -*-
from openerp import fields, models, api


def _available_action_types(self):
    return [('server', 'Send to Printer'),
            ('client', 'Send to Client'),
            ('user_default', "Use user's defaults"),
            ('location_default', "Use location's defaults"),
            ]


class PrintingAction(models.Model):
    _inherit = 'printing.action'

    type = fields.Selection(_available_action_types, required=True)


class PrintingPrinter(models.Model):
    _inherit = 'printing.printer'

    @api.one
    def name_get(self):
        loc = False
        if self.location:
            loc = ', {}'.format(self.location)
        return (self.id, '{}{}'.format(self.name, loc or ''))
