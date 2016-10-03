# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

class Procurement(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def run_scheduler(self, use_new_cursor=False, company_id = False):
        self.sudo().search([('state','=','exception')]).run(
            autocommit=use_new_cursor)
        return super(Procurement,self).run_scheduler(
            use_new_cursor=use_new_cursor,company_id=company_id
        )
