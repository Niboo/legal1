# -*- coding: utf-8 -*-

from openerp import fields, models
from openerp.addons.base_report_to_printer.printing import _available_action_types


class WorkLocation(models.Model):
    _name = 'work_location'
    _description = 'Work Location'

    name = fields.Char(required=True)
    work_location_printer_ids = fields.One2many('work_location_printer', 'work_location_id', 'Printers', required=False)


class work_location_printer(models.Model):
    _name = 'work_location_printer'
    _description = 'Printers'

    def _location_available_action_types(self):
        return [(code, string) for code, string
                in _available_action_types(self)
                if code != 'location_default']

    work_location_id = fields.Many2one('work_location', 'Work Location', required=False)
    printing_action = fields.Selection(_location_available_action_types)
    document_type_id = fields.Many2one(comodel_name='document_type',
                                          string='Document Type')
    printing_printer_id = fields.Many2one(comodel_name='printing.printer',
                                          string='Default Printer')


class document_type(models.Model):
    _name = 'document_type'
    _description = 'Document Type'

    name = fields.Char('Name', size=64, required=True)
