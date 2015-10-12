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

    def _get_location(self):
        for record in self:
            location = self.env['work_location_printer'].search([('printing_printer_id', '=', record.id)], limit=1)
            if location:
                record.location_id = location.work_location_id

    location_id = fields.Many2one('work_location', 'Location', compute='_get_location')

    @api.one
    def name_get(self):
        loc = False
        if self.location_id:
            loc = ', {}'.format(self.location_id.name)
        return (self.id, '{}{}'.format(self.name, loc or ''))
