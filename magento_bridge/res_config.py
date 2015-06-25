from openerp.osv import fields, osv
from openerp.tools.translate import _

class mob_config_settings(osv.osv_memory):
    _name = 'mob.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'mob_delivery_product': fields.many2one('product.product',"Delivery Product",
            help="""Service type product used for Delivery purposes."""),
        'mob_discount_product': fields.many2one('product.product',"Discount Product",
            help="""Service type product used for Discount purposes."""),
        'mob_coupon_product': fields.many2one('product.product',"Coupon Product",
            help="""Service type product used in Coupon."""),
    }
    def set_default_fields(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        config = self.browse(cr, uid, ids[0], context)
        ir_values.set_default(cr, uid, 'product.product', 'mob_delivery_product',
            config.mob_delivery_product and config.mob_delivery_product.id or False)
        ir_values.set_default(cr, uid, 'product.product', 'mob_discount_product',
            config.mob_discount_product and config.mob_discount_product.id or False)
        ir_values.set_default(cr, uid, 'product.product', 'mob_coupon_product',
            config.mob_coupon_product and config.mob_coupon_product.id or False)
        return True
    
    def get_default_fields(self, cr, uid, ids, context=None):
        values = {}
        ir_values = self.pool.get('ir.values')
        config = self.browse(cr, uid, ids[0], context)
        mob_delivery_product = ir_values.get_default(cr, uid, 'product.product', 'mob_delivery_product')
        mob_discount_product = ir_values.get_default(cr, uid, 'product.product', 'mob_discount_product')
        mob_coupon_product = ir_values.get_default(cr, uid, 'product.product', 'mob_coupon_product')
        return {'mob_discount_product':mob_discount_product,'mob_delivery_product':mob_delivery_product,'mob_coupon_product':mob_coupon_product}
mob_config_settings()