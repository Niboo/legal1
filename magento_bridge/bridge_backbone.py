 # -*- coding: utf-8 -*-
##############################################################################
#		
#    Odoo, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################

import time
import xmlrpclib
from openerp import workflow
from openerp import models, fields, api, _
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
from mob import _unescape
import logging

_logger = logging.getLogger(__name__)

class bridge_backbone(models.Model):
	_name="bridge.backbone"
	
	def create_pricelist(self, cr, uid, data, context=None):
		"""create and search pricelist by any webservice like xmlrpc.
		@param code: currency code.
		@param context: A standard dictionary
		@return: pricelist_id
		"""
		if context is None:
			context = {}
		currency_ids = self.pool.get('res.currency').search(cr,uid,[('name','=',data['code'])])  or [False]
		if currency_ids:
			pricelist_ids = self.pool.get('product.pricelist').search(cr,uid,[('currency_id','=',currency_ids[0])], context=context) or [False]
			if pricelist_ids[0] == False:
				pricelist_dict = {  'name': 'Mage_'+data['code'],
							   'active':True,
							   'type': 'sale',
							   'currency_id': currency_ids[0],
						   }
				pricelist_id = self.pool.get("product.pricelist").create(cr, uid, pricelist_dict, context)
				version_dict = {
								'name':data['code']+' Public Pricelist Version',
								'pricelist_id':pricelist_id,
								'active':True,
							}
				product_version_id = self.pool.get('product.pricelist.version').create(cr,uid,version_dict, context)
				price_type_id = self.pool.get('product.price.type').search(cr,uid,[('field','=','list_price')], context=context)			
				item_dict = {
								'name': data['code']+' Public Pricelist Line',
								'price_version_id': product_version_id,
								'base': price_type_id[0],
							}
				product_pricelist_item_id = self.pool.get('product.pricelist.item').create(cr, uid, item_dict,context)
				return pricelist_id
			else:
				return pricelist_ids[0]
		return False
	
	def _get_journal_code(self, cr, uid, string, sep=' ', context=None):
		tl = []
		for t in string.split(sep):
			t2 = t.title()[0]
			if t2.isalnum():
				tl.append(t2)
		code = ''.join(tl)
		code = code[0:3]
		is_exist = self.pool.get('account.journal').search(cr, uid, [('code', '=',code)], context=context)
		if is_exist:
			for i in range(1,99):
				is_exist = self.pool.get('account.journal').search(cr, uid, [('code', '=',code+str(i))], context=context)
				if not is_exist:
					return code+str(i)[-5:]
		return code
	
	def create_payment_method(self, cr, uid, data, context=None):
		"""create Journal by any webservice like xmlrpc.
		@param name: journal name.
		@param context: A standard dictionary
		@return: payment_id
		"""
		if context is None:
			context = {}
		payment_id = 0
		res = self.pool.get('account.journal').search(cr, uid, [('type', '=','cash')], limit=1, context=context)
		if res:
			credit_account_id = self.pool.get('account.journal').browse(cr, uid, res[0], context).default_credit_account_id.id
			debit_account_id = self.pool.get('account.journal').browse(cr, uid, res[0], context).default_debit_account_id.id
			data['default_credit_account_id'] = credit_account_id
			data['default_debit_account_id'] = debit_account_id
			data['code'] = self._get_journal_code(cr, uid, data.get('name'),' ', context)
			payment_id = self.pool.get('account.journal').create(cr, uid, data, context)
		return payment_id


	def _get_virtual_product_id(self, cr, uid, data):
		erp_product_id = False
		ir_values = self.pool.get('ir.values')
		if data['name'].startswith('S'):
			erp_product_id = ir_values.get_default(cr, uid, 'product.product', 'mob_delivery_product')
		if data['name'].startswith('D'):
			erp_product_id = ir_values.get_default(cr, uid, 'product.product', 'mob_discount_product')
		if data['name'].startswith('V'):
			erp_product_id = ir_values.get_default(cr, uid, 'product.product', 'mob_coupon_product')
		if not erp_product_id:
			temp_dic={'sale_ok':False, 'name':data.get('name'), 'type':'service', 'list_price':0.0}
			object_name = ''
			if data['name'].startswith('S'):
				object_name = 'mob_delivery_product'
				temp_dic['description']='Service Type product used by Magento Odoo Bridge for Shipping Purposes'
			if data['name'].startswith('D'):
				object_name = 'mob_discount_product'
				temp_dic['description']='Service Type product used by Magento Odoo Bridge for Discount Purposes'
			if data['name'].startswith('V'):
				object_name = 'mob_coupon_product'
				temp_dic['description']='Service Type product used by Magento Odoo Bridge for Gift Voucher Purposes'
			erp_product_id = self.pool.get('product.product').create(cr, uid, temp_dic)
			ir_values.set_default(cr, uid, 'product.product', object_name, erp_product_id)
			cr.commit()
		return erp_product_id

	def extra_order_line(self, cr, uid, data, context=None):
		"""create sale order line by any webservice like xmlrpc.
		@param data: dictionary of Odoo Order ID and line information.
		@param context: A standard dictionary
		@return: line_id
		"""
		if context is None:
			context = {}
		line_dic = {}
		sale_order_line = self.pool.get('sale.order.line')
		product_id = self._get_virtual_product_id(cr, uid, data)
		line_dic['product_id'] = product_id
		line_dic['order_id'] = data['order_id']
		line_dic['name'] = _unescape(data['description'])
		line_dic['price_unit'] = data['price_unit']
		line_dic['product_uom_qty'] = 1
		line_dic['product_uom'] = self.pool.get('product.product').browse(cr, uid, product_id).uom_id.id or 1
		if data.has_key('tax_id'):
			taxes = data.get('tax_id')
			if type(taxes) != list:
				taxes = [data.get('tax_id')]
			line_dic['tax_id'] = [(6,0,taxes)]
		else:
			line_dic['tax_id'] = False

		line_id = sale_order_line.create(cr, uid, line_dic, context)
		return line_id

	def create_order_line(self, cr, uid, data, context=None):
		"""create sale order line by any webservice like xmlrpc.
		@param data: dictionary of Odoo Order ID and line information.
		@param context: A standard dictionary
		@return: line_id
		"""
		if context is None:
			context = {}
		line_dic = {}
		product = self.pool.get('product.product')
		sale_order_line = self.pool.get('sale.order.line')
		if data.has_key('product_id'):
			line_dic['product_id'] = data.get('product_id')
			for route_id in product.browse(cr, uid, data.get('product_id')).route_ids:
				line_dic['route_id'] = int(route_id)
				break
			purchase_price = product.browse(cr, uid, data.get('product_id')).standard_price
			if purchase_price:
			 	line_dic['purchase_price'] = purchase_price
		if data.has_key('name') and data['name']:
			line_dic['name'] = _unescape(data.get('name'))
		if data.has_key('product_uom_qty'):
			line_dic['product_uom_qty'] = data.get('product_uom_qty')
		line_dic['product_uom'] = 1
		if data.has_key('price_unit'):
			line_dic['price_unit'] = data.get('price_unit')
		if data.has_key('discount'):
			line_dic['discount'] = data.get('discount')
		if data.has_key('order_id'):
			line_dic['order_id'] = data.get('order_id')
		if data.has_key('tax_id'):
			taxes = data.get('tax_id')
			if type(taxes) != list:
				taxes = [data.get('tax_id')]
			line_dic['tax_id'] = [(6,0,taxes)]
		else:
			line_dic['tax_id'] = False
			
		line_id = sale_order_line.create(cr, uid, line_dic, context)
		return line_id
	
	def sales_reorder(self, cr, uid, order_id, context=None):
		"""Create a new Copy of Quotation order by any webservice like xmlrpc.
		@param order_id: Odoo Order ID.
		@param context: A standard dictionary
		@return: newly created order id.
		"""
		reorder_id = self.pool.get('sale.order').copy_quotation(cr,uid,[order_id])['res_id']
		if reorder_id:
			self.pool.get('sale.order').signal_workflow(cr, uid, [reorder_id], 'order_confirm')
		return reorder_id
	
	def order_cancel(self,cr,uid,order_id,context=None):
		"""Cancel an order by any webservice like xmlrpc.
		@param order_id: Odoo Order ID.
		@param context: A standard dictionary
		@return: True
		"""
		if context is None:
			context = {}
		order_name=self.pool.get('sale.order').name_get(cr,uid,[order_id])		
		pick_id=self.pool.get('stock.picking').search(cr, uid,[('origin','=',order_name[0][1])])		
		if context.has_key('instance_id'):
			active_id = context.get('instance_id')
			state = self.pool.get('magento.configure').browse(cr, uid, active_id).state
			if state == 'enable':
				self.pool.get('magento.configure').write(cr, uid, active_id,{'state':'disable'})			
			order_obj = self.pool.get('sale.order').browse(cr, uid, order_id)
			pick_ids = order_obj.picking_ids
			for pick_obj in pick_ids:
				if pick_obj.state != "done":
					pick_cancel=self.pool.get('stock.picking').action_cancel(cr, uid, pick_obj.id)		
			order_cancel=self.pool.get('sale.order').action_cancel(cr,uid,[order_id])
			if state == 'enable':
				self.pool.get('magento.configure').write(cr, uid, active_id, {'state':'enable'})	
			return True
		return False
		
	def create_order_invoice(self, cr, uid, data, context=None):
		invoice_id = 0
		if data.get('order_id'):
			order_id = data['order_id']
			order_state = self.pool.get('sale.order').browse(cr, uid, order_id).state
			if order_state == 'draft':
				self.pool.get('sale.order').signal_workflow(cr, uid, [order_id],'order_confirm')
			
			if context.has_key('instance_id'):
				active_id = context.get('instance_id')
				state = self.pool.get('magento.configure').browse(cr, uid, active_id).state	
				if state == 'enable':
					self.pool.get('magento.configure').write(cr, uid, active_id,{'state':'disable'})
				sale_order_details = self.pool.get('sale.order').read(cr,uid,data.get('order_id'),['order_policy','invoice_ids'])
				if sale_order_details.get('order_policy') == 'prepaid':
					invoice_id = sale_order_details.get('invoice_ids')[0]
				else:
					inv_ids = self.pool.get('sale.order').manual_invoice(cr,uid,[data.get('order_id')])
					invoice_id = inv_ids['res_id']
				if invoice_id:
					if data.has_key('date'):
						self.pool.get('account.invoice').write(cr, uid,invoice_id,{'date_invoice':data.get('date'), 'date_due':data.get('date') ,'internal_number':data['mage_inv_number']})
					self.pool.get('account.invoice').signal_workflow(cr, uid, [invoice_id],'invoice_open')
				if state == 'enable':
					self.pool.get('magento.configure').write(cr, uid, active_id,{'state':'enable'})
				workflow.trg_validate(uid, 'sale.order',data.get('order_id'), 'invoice_end', cr)
		return invoice_id
		
		# code for Payment an order...... 
	def _get_journal_id(self, cr, uid, context=None):
		if context is None: context = {}
		if context.get('invoice_id', False):
			currency_id = self.pool.get('account.invoice').browse(cr, uid, context['invoice_id'], context=context).currency_id.id
			journal_id = self.pool.get('account.journal').search(cr, uid, [('currency', '=', currency_id)], limit=1)
			return journal_id and journal_id[0] or False
		res = self.pool.get('account.journal').search(cr, uid, [('type', '=','bank')], limit=1)
		return res and res[0] or False
	
	def _get_tax_id(self, cr, uid, journal_id, context=None):
		if context is None: context = {}
		journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
		account_id = journal.default_credit_account_id or journal.default_debit_account_id
		if account_id and account_id.tax_ids:
			tax_id = account_id.tax_ids[0].id
			return tax_id
		return False
	
	def _get_currency_id(self, cr, uid,journal_id,context=None):
		if context is None: context = {}
		journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
		if journal.currency:
			return journal.currency.id
		return self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
		
	def sales_order_payment(self, cr, uid, payment, context=None):	
		"""
		@param payment: List of invoice_id, reference, partner_id ,journal_id and amount
		@param context: A standard dictionary
		@return: True
		"""
		if context is None:
			context = {}
		voucher_obj = self.pool.get('account.voucher')
		voucher_line_obj = self.pool.get('account.voucher.line')
		partner_id = payment.get('partner_id')
		journal_id = payment.get('journal_id',False)
		if not journal_id:
			journal_id = self._get_journal_id(cr, uid, context)
		amount = payment.get('amount',0.0)
		date = payment.get('date',time.strftime('%Y-%m-%d'))
		entry_name = payment.get('reference') 
		currency_id1 = self._get_currency_id(cr, uid, journal_id)
		data = voucher_obj.onchange_partner_id(cr, uid, [], partner_id, journal_id,int(amount), currency_id1, 'receipt', date, context)['value']
		invoice_pool=self.pool.get('account.invoice')
		invoice_obj = invoice_pool.browse(cr,uid,payment.get('invoice_id'))
		invoice_name = invoice_obj.number
		for line_cr in data.get('line_cr_ids'):
			if line_cr['name'] == invoice_name:
				amount = line_cr['amount_original']
		account_id = data['account_id']
		statement_vals = {
							'reference': invoice_name+'('+entry_name+')',
                            'journal_id': journal_id,
                            'amount': amount,
                            'date' : date,
                            'partner_id': partner_id,
                            'account_id': account_id,
                            'company_id': invoice_obj.company_id.id,
                            'type': 'receipt',
                         }
		if data.get('payment_rate_currency_id'):
			statement_vals['payment_rate_currency_id'] = data['payment_rate_currency_id']
			company_currency_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
			if company_currency_id<>data['payment_rate_currency_id']:
				statement_vals['is_multi_currency']=True
	
		if data.get('paid_amount_in_company_currency'):
			statement_vals['paid_amount_in_company_currency'] = data['paid_amount_in_company_currency']
		if data.get('writeoff_amount'):
			statement_vals['writeoff_amount'] =data['writeoff_amount']
		if data.get('pre_line'):
			statement_vals['pre_line'] = data['pre_line']
		if data.get('payment_rate'):
			statement_vals['payment_rate'] = data['payment_rate']
		statement_id = voucher_obj.create(cr, uid, statement_vals, context)
		for line_cr in data.get('line_cr_ids'):
			line_cr.update({'voucher_id':statement_id})
			if line_cr['name'] == invoice_name:
				line_cr['amount'] = line_cr['amount_original']
				line_cr['reconcile'] = True
			line_cr_id=self.pool.get('account.voucher.line').create(cr, uid, line_cr)
		for line_dr in data.get('line_dr_ids'):
			line_dr.update({'voucher_id':statement_id})
			line_dr_id=self.pool.get('account.voucher.line').create(cr, uid, line_dr)

		self.pool.get('account.voucher').signal_workflow(cr, uid, [statement_id],'proforma_voucher')
		return True	
		
	# code for shipping an order......

	def order_shipped(self, cr, uid, data, context=None):
		if context is None:
			context = {}
		res = False
		context['stock_from'] = 'magento'
		order_id = data['order_id']
		order_obj = self.pool.get('sale.order').browse(cr, uid, order_id)
		order_state = order_obj.state
		if order_state == 'draft':
			self.pool.get('sale.order').signal_workflow(cr, uid, [order_id],'order_confirm')
			
		if context.has_key('instance_id'):
			active_id = context.get('instance_id')
			state = self.pool.get('magento.configure').browse(cr, uid, active_id).state
			if state == 'enable':
				self.pool.get('magento.configure').write(cr, uid, active_id, {'state': 'disable'})
			order_name = self.pool.get('sale.order').name_get(cr, uid, data['order_id'])		
			order_id = data['order_id']
			order_obj = self.pool.get('sale.order').browse(cr, uid, order_id)
			pick_ids = order_obj.picking_ids
			for pick_obj in pick_ids:
				status = pick_obj.state
				if status == "done":
					continue
				self.pool.get('stock.picking').do_transfer(cr, uid, pick_obj.id, context)
				self.pool.get('stock.picking').write(cr, uid, pick_obj.id,{'carrier_tracking_ref':data['carrier_tracking_ref'],'carrier_code':data['carrier_code'],'magento_shipment':data['mage_ship_number']} ,context)
			workflow.trg_validate(uid, 'sale.order',data['order_id'], 'ship_end', cr)
			res =  True
			if state == 'enable':
				self.pool.get('magento.configure').write(cr, uid, active_id, {'state': 'enable'})
			return res
		return False

	# code for update an inventry of a product...... 
	
	def update_quantity(self ,cr, uid, data, context=None):
		""" Changes the Product Quantity by making a Physical Inventory.
		@param self: The object pointer.
		@param cr: A database cursor
		@param uid: ID of the user currently logged in
		@param data: List of product_id and new_quantity
		@param context: A standard dictionary
		@return: True
		"""
		if context is None:
			context = {}
		location_id = 0	
		rec_id = data.get('product_id')
		mage_qty = data.get('new_quantity')
		context['stock_from'] = 'magento'
		prod_obj_pool = self.pool.get('product.product')
		assert rec_id, _('Active ID is not set in Context')
		if context.has_key('instance_id'):
			config_ids = context.get('instance_id')
			config_obj = self.pool.get('magento.configure').browse(cr, uid, config_ids)
			active = config_obj.active
			context['warehouse'] = config_obj.warehouse_id.id
			res_original = prod_obj_pool.browse(cr, uid, rec_id, context=context)		
			if active:
				warehouse_id = self.pool.get('magento.configure').browse(cr, uid, config_ids).warehouse_id.id
				location_id = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id).lot_stock_id.id	
			else:
				location_ids = self.pool.get('stock.warehouse').search(cr, uid, [], context=context)
				if location_ids:
					location_id = self.pool.get('stock.warehouse').browse(cr, uid, location_ids[0]).lot_stock_id.id			
			if int(mage_qty) == res_original.qty_available:
				return True
			elif int(mage_qty)< res_original.qty_available:
				product_qty_new = res_original.qty_available - int(mage_qty) 
				dest_location_id = self.pool.get('stock.location').search(cr, uid, [('usage','=','customer')],context=context)[0]
				line_data ={
					'product_uom_qty' : product_qty_new,
					'location_id' : location_id,
					'location_dest_id' : dest_location_id,
					'product_id' : rec_id,
					'product_uom' : res_original.uom_id.id,
					'name': res_original.name
				}
				move_obj = self.pool.get('stock.move')
				mv_id =  move_obj.create(cr , uid, line_data, context=context)
				move_obj.action_done(cr, uid, [mv_id], context=context)	

			elif int(mage_qty) > res_original.qty_available:
				inventory_obj = self.pool.get('stock.inventory')
				inventory_line_obj = self.pool.get('stock.inventory.line')
				product_qty_new = int(mage_qty) - res_original.qty_available
				inventory_id = inventory_obj.create(cr , uid, {'name': _('INV: %s') % tools.ustr(res_original.name)}, context=context)
				line_data ={
					'inventory_id' : inventory_id,
					'product_qty' : product_qty_new,
					'location_id' : location_id,
					'product_id' : rec_id,
					'product_uom_id' : res_original.uom_id.id
				}
				inventory_line_obj.create(cr , uid, line_data, context=context)

				inventory_obj.action_done(cr, uid, [inventory_id], context=context)
			return True
		return False

	def release_mage_order_from_hold(self, cr, uid, increment_id, url, session):
		server = xmlrpclib.Server(url)
		try:
			order_info = server.call(session,'order.info',[increment_id])
			if order_info['state'] == 'holded':
				server.call(session,'order.unhold',[increment_id])
			return  True
		except Exception,e:
			return False
	
bridge_backbone()
# END

