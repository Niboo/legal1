# -*- coding: utf-8 -*-


def migrate(cr, version):
    """
    Gain a little performance by setting picking_started for some known
    pickings """
    cr.execute(
        """
        UPDATE stock_picking sp, stock_move sm
        SET sp.picking_started = true
        WHERE sm.picking_id = sp.id
        AND sm.state in ('done', 'assigned')
        """)
