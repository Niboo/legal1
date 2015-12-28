# -*- coding: utf-8 -*-
import threading
from openerp import models, api


class Report(models.Model):
    _inherit = 'report'

    @api.v7
    def _print_document_async(self, cr, uid, ids, report, context):
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self.pool['report'].print_document(
                new_cr, uid, ids, report, context=context)
            new_cr.close()

    @api.v7
    def print_document_async(self, cr, uid, ids, report, context=None):
        return self.print_document(cr, uid, ids, report, context=context)
        # Disable async reporting as this results in a fork bomb that exhausts
        # the available database connections. To be refactored into a proper
        # print queue using the connector framework for example.
        threading.Thread(
            target=self._print_document_async,
            args=(cr, uid, ids, report, context)).start()

    @api.v8
    def print_document_async(self, record, report):
        return self.print_document(record, report)
        # Disable async reporting as this results in a fork bomb that exhausts
        # the available database connections. To be refactored into a proper
        # print queue using the connector framework for example.
        threading.Thread(
            target=self.pool['report']._print_document_async,
            args=(self.env.cr, self.env.uid, record.ids, report,
                  self.env.context)).start()
