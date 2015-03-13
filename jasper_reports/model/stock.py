from openerp.osv import orm, osv, fields

class stock_picking(osv.osv):

    _inherit = "stock.picking"

    def _prepare_invoice_group(self, cr, uid, picking, partner, invoice, context=None):
        result = super(stock_picking,self)._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
        result.update({'xx_picking_ids': [(4, picking.id)]})
        return result

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        result = super(stock_picking,self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        result.update({'xx_picking_ids': [(6,0,[picking.id])]})
        return result

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=None):
        result = super(stock_picking,self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=context)
        result.update({'xx_picking_ids': [(6,0,[picking.id])]})
        if move_line.sale_line_id:
            result.update({'sequence': move_line.sale_line_id.sequence})
        return result

class stock_picking_out(osv.osv):

    _inherit = "stock.picking"

    _columns = {
        'xx_invoice_ids': fields.many2many('account.invoice', 'stock_picking_out_invoice_rel', 'picking_id', 'invoice_id', 'Invoices', readonly=True),
        'xx_invoice_line_ids': fields.many2many('account.invoice.line', 'stock_picking_out_invoice_line_rel', 'picking_id', 'invoice_line_id', 'Invoice Lines', readonly=True),
    }
