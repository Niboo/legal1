# -*- coding: utf-8 -*-
from openerp import api, models, fields


class Picking(models.Model):
    _inherit = 'stock.picking'

    search_last_user = fields.Many2one(
        'res.users', compute="compute_dummy",
        search="_search_last_user")

    @api.model
    def _search_last_user(self, operator, value):
        users = self.env['res.users'].search([('name', operator, value)])
        if not users:
            return []
        self.env.cr.execute(
            """
            SELECT p.id
            FROM stock_picking p,
                 stock_move sm
            WHERE sm.picking_id = p.id
                AND sm.write_uid in %s
            """, (tuple(users.ids),))
        return [('id', 'in', [row[0] for row in self.env.cr.fetchall()])]

    @api.multi
    def compute_dummy(self):
        for picking in self:
            self.search_last_user = False
