 # -*- coding: utf-8 -*-
##############################################################################
#		
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import tools
import time
import openerp.pooler
import openerp.netsvc
import xmlrpclib
from datetime import date
	
class stock_change_product_qty(osv.osv_memory):
	_inherit= 'stock.change.product.qty'
	
	def change_product_qty(self, cr, uid, ids, context=None):
		""" Changes the Product Quantity by making a Physical Inventory.
		@param self: The object pointer.
		@param cr: A database cursor
		@param uid: ID of the user currently logged in
		@param ids: List of IDs selected
		@param context: A standard dictionary
		@return:
		"""
		if context is None:
			context = {}

		rec_id = context and context.get('active_id', False)
		assert rec_id, _('Active ID is not set in Context')

		inventory_obj = self.pool.get('stock.inventory')
		inventory_line_obj = self.pool.get('stock.inventory.line')
		prod_obj_pool = self.pool.get('product.product')
		
		# code for update required in mapping
		map_ids = self.pool.get('magento.product').search(cr,uid,[('pro_name','=',rec_id)])
		if map_ids:
			self.pool.get('magento.product').write(cr, uid, map_ids[0], {'need_sync':'Yes'})

		for data in self.browse(cr, uid, ids, context=context):
			if data.new_quantity < 0:
				raise osv.except_osv(_('Warning!'), _('Quantity cannot be negative.'))
			ctx = context.copy()
			ctx['location'] = data.location_id.id
			ctx['lot_id'] = data.lot_id.id
			res_original = prod_obj_pool.browse(cr, uid, rec_id, context=ctx)
			inventory_id = inventory_obj.create(cr, uid, {'name': _('INV: %s') % tools.ustr(res_original.name), 'product_id': rec_id, 'location_id': data.location_id.id, 'lot_id': data.lot_id.id}, context=context)
			th_qty = res_original.qty_available
			line_data = {
                'inventory_id': inventory_id,
                'product_qty': data.new_quantity,
                'location_id': data.location_id.id,
                'product_id': rec_id,
                'product_uom_id': res_original.uom_id.id,
                'th_qty': th_qty,
                'prod_lot_id': data.lot_id.id
            }
			inventory_line_obj.create(cr , uid, line_data, context=context)
			inventory_obj.action_done(cr, uid, [inventory_id], context=context)
		return {}
		
stock_change_product_qty()