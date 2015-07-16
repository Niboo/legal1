 # -*- coding: utf-8 -*-
##############################################################################
#		
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################

import sys 
import openerp.pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import datetime
import xmlrpclib
import urllib
import openerp.tools


################## .............magento-Odoo stock.............##################

class stock_move(osv.osv):
	_inherit="stock.move"

	def action_done(self, cr, uid, ids, context=None):
		""" Process completly the moves given as ids and if all moves are done, it will finish the picking.
		"""
		res = super(stock_move, self).action_done(cr, uid, ids, context)
		if context.has_key('stock_from') and context['stock_from'] == 'magento':
			return res
		for id in ids:	
			data=self.browse(cr,uid,id)
			erp_product_id = data.product_id.id
			flag = 1
			if data.origin!=False:
				if data.origin.startswith('SO'):
					sale_id = self.pool.get('sale.order').search(cr,uid,[('name','=',data.origin)])
					if sale_id:
						get_channel = self.pool.get('sale.order').browse(cr,uid,sale_id[0]).channel
						if get_channel == 'magento':
							flag=0
			else:
				flag = 2 # no origin
			product_qty = 0
			warehouse_id = 1
			if flag == 1:
				product_qty = int(data.product_qty)
				if 'OUT' in data.picking_id.name:
					product_qty = int(-product_qty)
					warehouse_id = data.company_id.id
			if flag == 2:				
				check_in = self.pool.get('stock.warehouse').search(cr,uid,[('lot_stock_id','=',data.location_dest_id.id),('company_id','=',data.company_id.id)],limit=1)
				if check_in:
					# Getting Goods.
					warehouse_id = check_in[0]
					product_qty=int(data.product_qty)
				check_out = self.pool.get('stock.warehouse').search(cr,uid,[('lot_stock_id','=',data.location_id.id),('company_id','=',data.company_id.id)],limit=1)
				if check_out:
					# Sending Goods.
					warehouse_id = check_out[0]
					product_qty=int(-data.product_qty)					
			self.check_warehouse(cr, uid, erp_product_id, warehouse_id, product_qty)

	def check_warehouse(self, cr, uid, erp_product_id, warehouse_id, product_qty, context=None):
		mapping_ids = self.pool.get('magento.product').search(cr, uid, [('pro_name','=',erp_product_id)])
		if mapping_ids:
			mapping_obj = self.pool.get('magento.product').browse(cr, uid, mapping_ids[0])
			instance_id = mapping_obj.instance_id.id				
			if mapping_obj.instance_id.warehouse_id.id == warehouse_id:					
				self.synch_quantity(cr, uid, erp_product_id, product_qty, instance_id, warehouse_id)
			

	def synch_quantity(self, cr, uid, erp_product_id, product_qty, instance_id, context=None):
		response=self.update_quantity(cr,uid,erp_product_id,product_qty, instance_id)
		if response[0]==1:
			return True
		else:
			self.pool.get('magento.sync.history').create(cr,uid,{'status':'no','action_on':'product','action':'c','error_message':response[1]})
		
	def update_quantity(self, cr, uid, erp_product_id, quantity, instance_id):
		session = 0
		text = ''
		stock = 0
		qty = 0		
		check_mapping = self.pool.get('magento.product').search(cr,uid,[('pro_name','=',erp_product_id),('instance_id','=',instance_id)])
		if check_mapping:
			map_obj = self.pool.get('magento.product').browse(cr,uid,check_mapping[0])
			mage_product_id = map_obj.mag_product_id
			obj = self.pool.get('magento.configure').browse(cr, uid, instance_id)		
			if not obj.active :
				return [0,' Connection needs one Active Configuration setting.']
			else:
				url = obj.name+'/index.php/api/xmlrpc'
				user = obj.user
				pwd = obj.pwd
				try:
					server = xmlrpclib.Server(url)
					session = server.login(user,pwd)
				except xmlrpclib.Fault, e:
					text = 'Error, %s Magento details are Invalid.'%e
				except IOError, e:
					text = 'Error, %s.'%e
				except Exception,e:
					text = 'Error in Magento Connection.'
				if not session:
					return [0,text]
				else:
					try:
						stock_search = server.call(session, 'product_stock.list', [mage_product_id])
						qty = int(float(stock_search[0]['qty']))
					except Exception,e:
						return [0,' Unable to search stock for product id %s'%mage_product_id]
					if type(quantity)==str:
							quantity = quantity.split('.')[0]
					if type(quantity)==float:
						quantity = quantity.as_integer_ratio()[0]
					try:
						qty = qty + quantity
						if qty>0:
							stock = 1
						server.call(session, 'product_stock.update', [mage_product_id,{'manage_stock':1, 'qty':qty,'is_in_stock':stock}])
						return [1,'']
					except Exception,e:
						return [0,' Error in Updating Quantity for Magneto Product Id %s.'%mage_product_id]
		else:
			return [0,'Error in Updating Stock, OE Product Id %s not found in Mapping table.'%erp_product_id]
stock_move()	