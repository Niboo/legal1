# -*- coding: utf-8 -*-
from openerp import models, fields

from .printing import _available_action_types


class ReportXmlAction(models.Model):
    _inherit = 'printing.report.xml.action'

    action = fields.Selection(_available_action_types,
                              required=True)
