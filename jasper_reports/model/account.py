from openerp.osv import orm, osv, fields
import openerp.addons.decimal_precision as dp

class account_invoice(osv.osv):

    _inherit = "account.invoice"

    _columns = {
        'xx_sale_ids': fields.many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Sale Orders', readonly=True, ),
        'xx_picking_ids': fields.many2many('stock.picking', 'stock_picking_out_invoice_rel', 'invoice_id','picking_id', 'Delivery Orders', readonly=True),
    }

class account_invoice_line(osv.osv):

    _inherit = "account.invoice.line"

    _columns = {
        'xx_sale_line_ids': fields.many2many('sale.order.line', 'sale_order_line_invoice_rel', 'invoice_id','order_line_id', 'Sale Order Lines', readonly=True),
        'xx_picking_ids': fields.many2many('stock.picking', 'stock_picking_out_invoice_line_rel', 'invoice_line_id','picking_id', 'Delivery Orders', readonly=True),
    }

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        invoice = self.pool.get('account.invoice').browse(cr, uid, ids[0], context=context)
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
             'ids': ids,
             'model': 'account.invoice',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        return self.pool.get('res.partner').get_report(cr, uid, [invoice.partner_id.id], 'invoice', datas, context=context)

class account_tax(osv.osv):

    _inherit = 'account.tax'

    def _get_tax_val(self, cr, uid, ids, field_name, arg, context=None):
        account_taxes = self.browse(cr, uid, ids)
        result = {}
        
        for account_tax in account_taxes:
            result[account_tax.id] = account_tax.amount * 100.0        
        return result

    _columns = {
        'xx_tax_val': fields.function(_get_tax_val, type="float", string="TAX value", digits_compute=dp.get_precision('Account')),
        }