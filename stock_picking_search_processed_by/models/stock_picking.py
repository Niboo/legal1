# -*- coding: utf-8 -*-
from openerp import api, models, fields


class Picking(models.Model):
    _inherit = 'stock.picking'

    search_last_user = fields.Many2one(
        'res.users', compute="compute_dummy",
        search="_search_last_user")

    @api.model
    def _search_last_user(self, operator, value):
        """ Lots of operator/value combinations are not covered in this search
        method, but we are only interested in ('ilike', 'eltj') and ('=', 76)
        """
        if value and isinstance(value, (int, long)):
            user_ids = [value]
        else:
            user_ids = self.env['res.users'].search(
                [('name', operator, value)]).ids
            if not user_ids:
                return []
        self.env.cr.execute(
            """
            SELECT p.id
            FROM stock_picking p,
                 stock_move sm,
                 stock_move sm2
            WHERE sm.picking_id = p.id
                AND sm.group_id IS NOT NULL
                AND sm.group_id = sm2.group_id
                AND sm2.write_uid in %s
            """, (tuple(user_ids),))
        return [('id', 'in', [row[0] for row in self.env.cr.fetchall()])]

    @api.multi
    def compute_dummy(self):
        for picking in self:
            picking.search_last_user = False
