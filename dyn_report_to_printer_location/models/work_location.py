# -*- coding: utf-8 -*-

from openerp import fields, models
from openerp.addons.base_report_to_printer.printing import _available_action_types


class WorkLocation(models.Model):
    _name = 'work_location'
    _description = 'Work Location'

    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', 'Current/Last User', compute='_compute_user_id')
    work_location_printer_ids = fields.One2many('work_location_printer', 'work_location_id', 'Printers', required=False)

    def _compute_user_id(self):
        for rec in self:
            user = self.env['res.users'].search([('work_location_id', '=', rec.id)])
            rec.user_id = user.id


class work_location_printer(models.Model):
    _name = 'work_location_printer'
    _description = 'Printers'

    def _location_available_action_types(self):
        return [(code, string) for code, string
                in _available_action_types(self)
                if code != 'location_default']

    work_location_id = fields.Many2one('work_location', 'Work Location', required=True)
    printing_action = fields.Selection(_location_available_action_types, required=True)
    document_type_id = fields.Many2one(comodel_name='document_type',
                                          string='Document Type', required=True)
    printing_printer_id = fields.Many2one(comodel_name='printing.printer',
                                          string='Default Printer')


class document_type(models.Model):
    _name = 'document_type'
    _description = 'Document Type'

    name = fields.Char('Name', size=64, required=True)
