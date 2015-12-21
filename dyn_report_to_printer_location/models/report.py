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
        threading.Thread(
            target=self._print_document_async,
            args=(cr, uid, ids, report, context)).start()

    @api.v8
    def print_document_async(self, record, report):
        threading.Thread(
            target=self._print_document_async,
            args=(self.env.cr, self.env.uid, record.ids, report,
                  self.env.context)).start()
