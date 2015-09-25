# -*- coding: utf-8 -*-

from openerp import fields, models
from openerp.tools.sql import drop_view_if_exists


class report_picking_wave(models.Model):
    _name = 'report.picking.wave'
    _description = 'Picking Wave Report'
    _auto = False
    # _order = 'location_id'

    location_id = fields.Many2one('stock.location', 'Location', required=True)
    quant_id = fields.Many2one('stock.quant', 'Quant', required=True)
    move_id = fields.Many2one('stock.move', 'Stock Move', required=True)
    picking_id = fields.Many2one('stock.picking', 'Picking', required=True)
    wave_id = fields.Many2one('stock.wave', 'Picking Wave', required=True)

    def init(self, cr):
        drop_view_if_exists(cr, 'report_picking_wave')
        cr.execute("""
            CREATE OR REPLACE VIEW report_picking_wave as (
                SELECT
                    l.id AS location_id,
                    q.id AS quant_id,
                    m.id AS move_id,
                    p.id AS picking_id,
                    w.id AS wave_id
                FROM stock_quant q
                INNER JOIN stock_location l ON q.location_id = l.id
                INNER JOIN stock_move m ON q.reservation_id = m.id
                INNER JOIN stock_picking p ON m.picking_id = p.id
                INNER JOIN stock_picking_wave w ON p.wave_id = w.id
                ORDER BY l.name ASC
            );""")
