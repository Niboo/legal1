from openerp import models, fields, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    @api.depends('move_dest_id')
    def _get_tracking_fields(self):
        """ Retrieve the ultimate destination move, if any. From any
        procuring move, this allows easy retrieval to a related MTO sale order,
        if any, as well as some other linked resources."""

        def get_source(proc):
            procs = self.search(
                [('move_dest_id', 'in', proc.move_ids.ids)])
            if procs:
                # Prefer a non cancelled procurement
                return (procs.filtered(
                    lambda p: p.state != 'cancel') or procs)[0]
            return self.browse([])

        for proc in self:
            proc.source_procurement_id = get_source(proc)
            source = proc.source_procurement_id
            while source:
                proc.ultimate_source_procurement_id = source
                source = get_source(source)
            proc.ultimate_purchase_id = proc.ultimate_source_procurement_id\
                                            .purchase_id or proc.purchase_id
            proc.ultimate_dest_procurement_id = (
                proc.move_dest_id.procurement_id)
            while proc.ultimate_dest_procurement_id.move_dest_id\
                                                   .procurement_id:
                proc.ultimate_dest_procurement_id = (
                    proc.ultimate_dest_procurement_id.move_dest_id
                    .procurement_id)
            proc.ultimate_sale_line_id = proc.ultimate_dest_procurement_id\
                                             .sale_line_id or proc.sale_line_id
            if proc.move_ids:
                proc.source_move_id = proc.move_ids[0]
            else:
                proc.source_move_id = False

    dest_procurement_id = fields.Many2one(
        'procurement.order',
        string='Next destination procurement',
        related='move_dest_id.procurement_id',
        readonly=True)
    ultimate_dest_procurement_id = fields.Many2one(
        'procurement.order', string='Ultimate destination procurement',
        compute="_get_tracking_fields")
    source_procurement_id = fields.Many2one(
        'procurement.order',
        string='Next source procurement',
        compute="_get_tracking_fields")
    ultimate_source_procurement_id = fields.Many2one(
        'procurement.order',
        string='Ultimate source procurement',
        compute="_get_tracking_fields")
    ultimate_sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Destination sale line',
        compute="_get_tracking_fields")
    ultimate_purchase_id = fields.Many2one(
        'purchase.order',
        string='Ultimate purchase order',
        compute="_get_tracking_fields")
    source_move_id = fields.Many2one(
        'stock.move',
        compute='_get_tracking_fields',
        string='Source move')
