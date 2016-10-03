# -*- coding: utf-8 -*-
from openerp import models, fields, api


class ReportXml(models.Model):
    _inherit = 'ir.actions.report.xml'

    document_type_id = fields.Many2one(
        'document_type', 'Document Type', required=False)

    @api.multi
    def behaviour(self):
        result = {}
        printer_obj = self.env['printing.printer']
        printing_act_obj = self.env['printing.report.xml.action']
        # Set hardcoded default action
        default_action = 'client'
        # Retrieve system wide printer
        default_printer = printer_obj.get_default()

        # Retrieve user default values
        user = self.env.user
        if user.printing_action:
            default_action = user.printing_action
        if user.printing_printer_id:
            default_printer = user.printing_printer_id

        for report in self:
            action = default_action
            printer = default_printer
            report_action = report.property_printing_action

            # Override user defaults with location defaults
            work_location = self.env.user.work_location_id
            if not work_location and self.env.user.reset_work_location:
                # Force get_pdf by setting action to False
                result[report.id] = {
                    'printer': default_printer, 'action': False}
                continue
            if (work_location and report_action and
                    report_action.type == 'location_default'):
                for wl_printer in work_location.work_location_printer_ids:
                    if wl_printer.document_type_id == report.document_type_id:
                        if wl_printer.printing_action:
                            action = wl_printer.printing_action
                        if wl_printer.printing_printer_id:
                            printer = wl_printer.printing_printer_id
                        break

            # Retrieve report default values
            if report_action and report_action.type not in (
                    'user_default', 'location_default'):
                action = report_action.type
            if report.printing_printer_id:
                printer = report.printing_printer_id

            # Retrieve report-user specific values
            print_action = printing_act_obj.search(
                [('report_id', '=', report.id),
                 ('user_id', '=', self.env.uid),
                 ('action', '!=', 'user_default')],
                limit=1)
            if print_action:
                user_action = print_action.behaviour()
                action = user_action['action']
                if user_action['printer']:
                    printer = user_action['printer']

            result[report.id] = {'action': action,
                                 'printer': printer,
                                 }
            print action
            print printer.name
        return result
