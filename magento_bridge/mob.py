 # -*- coding: utf-8 -*-
##############################################################################
#		
#    Odoo, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################

import re
import xmlrpclib
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
from ..base.res.res_partner import _lang_get
import logging
_logger = logging.getLogger(__name__)

XMLRPC_API = '/index.php/api/xmlrpc'

def _unescape(text):
	##
	# Replaces all encoded characters by urlib with plain utf8 string.
	#
	# @param text source text.
	# @return The plain text.
	from urllib import unquote_plus
	return unquote_plus(text.encode('utf8'))

class magento_website(osv.osv):
	_name = "magento.website"
	_description = "Magento Website"
	_columns = {
		'name':fields.char('Website Name', size=64, required=True),
		'website_id':fields.integer('Magento Webiste Id', readonly=True),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'code':fields.char('Code', size=64, required=True),
		'sort_order':fields.char('Sort Order', size=64),
		'is_default':fields.boolean('Is Default', readonly=True),
		'default_group_id':fields.integer('Default Store', readonly=True),
		'create_date':fields.datetime('Created Date', readonly=True),
	}

	def _get_website(self, cr, uid, website, context=None):
		website_id = 0
		instance_id = context.get('instance_id')		
		websites = self.search(cr, uid, [('website_id','=',website['website_id']),('instance_id','=',instance_id)])		
		if websites:
			website_id = websites[0]
		else:
			website_dict = {
							'name':website['name'],
							'code':website['code'],
							'instance_id':instance_id,
							'website_id': website['website_id'],
							'is_default':website['is_default'],
							'sort_order':website['sort_order'],
							'default_group_id':website['default_group_id']
						}
			website_id = self.create(cr, uid, website_dict)			
		return website_id

magento_website()


class magento_store(osv.osv):
	_name = "magento.store"
	_description = "Magento Store"
	_columns = {
		'name':fields.char('Store Name', size=64, required=True),
		'group_id':fields.integer('Magento Store Id', readonly=True),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'root_category_id':fields.integer('Root Category Id', readonly=True),
		'default_store_id':fields.integer('Default Store Id'),
		'website_id':fields.many2one('magento.website','Website Id'),
		'create_date':fields.datetime('Created Date', readonly=True),
	}

	def _get_store_group(self, cr, uid, group, website, context=None):
		group_id = 0
		instance_id = context.get('instance_id')
		website_pool = self.pool.get('magento.website')		
		groups = self.search(cr, uid, [('group_id','=',group['group_id']),('instance_id','=',instance_id)])
		if groups:
			group_id = groups[0]
		else:
			website_id = website_pool._get_website(cr, uid, website, context)
			group_dict = {
							'name':group['name'],
							'website_id': website_id,
							'group_id': group['group_id'],
							'instance_id':instance_id,
							'root_category_id': group['root_category_id'],
							'default_store_id': group['default_store_id'],
						}
			group_id = self.create(cr, uid, group_dict)
		return group_id

magento_store()

class magento_store_view(osv.osv):
	_name = "magento.store.view"
	_description = "Magento Store View"
	_columns = {
		'name':fields.char('Store View Name', size=64, required=True),
		'code':fields.char('Code', size=64, required=True),
		'view_id':fields.integer('Magento Store View Id', readonly=True),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'group_id':fields.many2one('magento.store','Store Id'),
		'is_active':fields.boolean('Active'),
		'sort_order':fields.integer('Sort Order'),
		'create_date':fields.datetime('Created Date', readonly=True),
	}

	def name_get(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		if isinstance(ids, (int, long)):
			ids = [ids]
		res = []
		for record in self.browse(cr, uid, ids, context=context):
			name = record.name
			if record.group_id:
				name = name + "\n(%s)"%(record.group_id.name) + "\n(%s)"%(record.group_id.website_id.name)
			res.append((record.id, name))
		return res

	def _get_store_view(self, cr, uid, store, context=None):
		group_id = 0
		instance_id = context.get('instance_id')
		group_pool = self.pool.get('magento.store')		
		views = self.search(cr, uid, [('view_id','=',store['store_id']),('instance_id','=',instance_id)])
		if views:
			view_id = views[0]
		else:
			group_id = group_pool._get_store_group(cr, uid, store['group'], store['website'], context)
			view_dict = {
							'name':store['name'],
							'code':store['code'],
							'view_id':store['store_id'],
							'group_id':group_id,
							'instance_id':instance_id,
							'is_active': store['is_active'],
							'sort_order': store['sort_order'],
						}
			view_id = self.create(cr, uid, view_dict)			
		return view_id

magento_store_view()

class magento_configure(osv.osv):
	_name = "magento.configure"
	_inherit = ['mail.thread']
	_description = "Magento Configuration"
	_rec_name = 'instance_name'	
		
	def _default_category(self, cr, uid, context=None):
		if context is None:
			context = {}
		if 'categ_id' in context and context['categ_id']:
			return context['categ_id']
		md = self.pool.get('ir.model.data')
		res = False
		try:
			res = md.get_object_reference(cr, uid, 'product', 'product_category_all')[1]
		except ValueError:
			res = False
		return res

	def _default_instance_name(self, cr, uid, context=None):
		if context is None:
			context = {}
		res = self.pool.get('ir.sequence').get(cr, uid, 'magento.configure')
		return res

	def _fetch_magento_store(self, cr, uid, url, session, context=None):
		if context is None:
			context = {}
		stores = []
		store_info = {}
		view_pool = self.pool.get('magento.store.view')
		try:
			server = xmlrpclib.Server(url)
			stores = server.call(session, 'store.list')
		except xmlrpclib.Fault, e:
			raise osv.except_osv(_('Error'), _("Error While Fetching Magento Stores!!!, %s")%e)
		for store in stores:
			if store['website']['is_default'] == '1':				
				store_info['website_id'] = int(store['website']['website_id'])
				store_info['store_id'] = view_pool._get_store_view(cr, uid, store, context)
				break;
		return store_info


	_columns = {
		'name': fields.char('Base URL', required=True, size=255 ,select=True),
		'instance_name': fields.char("Instance Name",size=64,select=True),
		'user':fields.char('API User Name', required=True, size=100),
		'pwd':fields.char('API Password',required=True, size=100),
		'status':fields.char('Connection Status',readonly=True, size=255),
		'active':fields.boolean('Active'),
		'store_id':fields.many2one('magento.store.view', 'Default Magento Store'),
		'group_id':fields.related('store_id', 'group_id', type="many2one", relation="magento.store", string="Default Store", readonly=True, store=True),
		'website_id':fields.related('group_id', 'website_id', type="many2one", relation="magento.website", string="Default Magento Website", readonly=True),
		'credential':fields.boolean('Show/Hide Credentials Tab', 
							help="If Enable, Credentials tab will be displayed, "
							"And after filling the details you can hide the Tab."),
		'auto_invoice':fields.boolean('Auto Invoice',
							help="If Enabled, Order will automatically Invoiced on Magento "
								" when Odoo order Get invoiced."),
		'auto_ship':fields.boolean('Auto Shipment', 
							help="If Enabled, Order will automatically shipped on Magento" 
								" when Odoo order Get Delivered."),
		'notify':fields.boolean('Notify Customer By Email', 
							help="If True, customer will be notify" 
								"during order shipment and invoice, else it won't."),
		'language':fields.selection(_lang_get, "Default Language", help="Selected language is loaded in the system, "
							"all documents related to this contact will be synched in this language."),
		'category':fields.many2one('product.category', "Default Category", help="Selected Category will be set default category for odoo's product, "
							"in case when magento product doesn\'t belongs to any catgeory."),
		'state':fields.selection([('enable','Enable'),('disable','Disable')],'Status', help="status will be consider during order invoice, "
							"order delivery and order cancel, to stop asynchronous process at other end.", size=100),
		'inventory_sync':fields.selection([	('enable','Enable'),
											('disable','Disable')],
								'Inventory Update', 
								help="If Enable, Invetory will Forcely Update During Product Update Operation.", size=100),
		'warehouse_id':fields.many2one('stock.warehouse','Warehouse', 
									help="Used During Inventory Synchronization From Magento to Odoo."),
		'create_date':fields.datetime('Created Date'),
	}
	_defaults = {
		'instance_name':_default_instance_name,
		'active':lambda *a: 1,	
		'auto_ship':lambda *a: 1,
		'auto_invoice':lambda *a: 1,
		'credential':lambda *a: 1,
		'language': api.model(lambda self: self.env.lang),
		'category':_default_category,
		'state':'enable',
		'inventory_sync':'enable',
		'notify':lambda *a: 1,
		'warehouse_id':lambda self, cr, uid, c: self.pool.get('sale.order')._get_default_warehouse(cr, uid, context=c),
	}
	
	def create(self, cr, uid, vals, context=None):
		active_ids = self.pool.get('magento.configure').search(cr, uid, [('active','=',True)])		
		if vals['active']:
			if active_ids:
				raise osv.except_osv(_('Warning'), _("Sorry, Only one active connection is allowed."))
		#vals['instance_name'] = self.pool.get('ir.sequence').get(cr, uid, 'magento.configure')
		return super(magento_configure, self).create(cr, uid, vals, context=context)

	def write(self, cr, uid, ids, vals, context=None):
		active_ids = self.pool.get('magento.configure').search(cr, uid, [('active','=',True)])		
		instance_value = self.browse(cr, uid, ids)
		if vals:
			if instance_value.instance_name == None or instance_value.instance_name == False:
				vals['instance_name'] = self.pool.get('ir.sequence').get(cr, uid, 'magento.configure')
			if len(active_ids)>0 and vals.has_key('active') and vals['active']:
				raise osv.except_osv(_('Warning'), _("Sorry, Only one active connection is allowed."))
		return super(magento_configure, self).write(cr, uid, ids, vals, context=context)

	def fetch_connection_info(self, cr, uid, vals):
		"""
			Called by Xmlrpc from Magento
		"""
		mage_url = re.sub(r'^https?:\/\/', '', vals.get('magento_url'))
		active_connection_id = self.search(cr, uid, [('active','=',True)])
		for odoo_id in active_connection_id:
			act =self.browse(cr, uid, odoo_id).name
			act = re.sub(r'^https?:\/\/', '', act)
			active_connection_data = {}
			if mage_url == act or mage_url[:-1] == act:
				active_connection_data = self.read(cr, uid, odoo_id, ['language', 'category', 'warehouse_id'])				
				return active_connection_data
		return False

	def set_default_magento_website(self, cr, uid, ids, url, session, context=None):
		if context is None:
			context = {}
		for obj in self.browse(cr, uid, ids):
			store_id = obj.store_id
			context['instance_id'] = obj.id
			if not store_id:
				store_info = self._fetch_magento_store(cr, uid, url, session, context)
				if store_info:
					self.write(cr, uid, ids, store_info, context)
				else:
					raise osv.except_osv(_('Error'), _("Magento Default Website Not Found!!!"))
		return True
	
	#############################################
	##    		magento connection		   	   ##
	#############################################
	def test_connection(self, cr, uid, ids, context=None):
		session = 0
		status = 'Magento Connection Un-successful'
		text = 'Test connection Un-successful please check the magento api credentials!!!'
		obj = self.browse(cr, uid, ids[0])
		url = obj.name + XMLRPC_API
		user = obj.user
		pwd = obj.pwd
		try:
			server = xmlrpclib.Server(url)
			session = server.login(user, pwd)
		except xmlrpclib.Fault, e:
			text = "Error, %s Invalid Login Credentials!!!"%(e.faultString)
		except IOError, e:
			text = str(e)
		except Exception,e:
			text = "Magento Connection Error in connecting: %s"%(e)
		if session:
			store_id = self.set_default_magento_website(cr, uid, ids, url, session)
			text = 'Test Connection with magento is successful, now you can proceed with synchronization.'
			status = "Congratulation, It's Successfully Connected with Magento Api."
		self.write(cr, uid, ids[0],{'status':status})
		partial = self.pool.get('message.wizard').create(cr, uid, {'text':text})
		return { 'name':_("Information"),
				 'view_mode': 'form',
				 'view_id': False,
				 'view_type': 'form',
				'res_model': 'message.wizard',
				 'res_id': partial,
				 'type': 'ir.actions.act_window',
				 'nodestroy': True,
				 'target': 'new',
				 'domain': '[]',
			 }

	def _create_connection(self, cr, uid, context=None):
		""" create a connection between Odoo and magento 
			returns: False or list"""
		session = 0
		instance_id = 0
		if context.has_key('instance_id'):
			instance_id = context.get('instance_id')
		else:
			config_id = self.search(cr, uid, [('active','=',True)])
			if len(config_id) > 1:
				raise osv.except_osv(_('Error'), _("Sorry, only one Active Configuration setting is allowed."))
			if not config_id:
				raise osv.except_osv(_('Error'), _("Please create the configuration part for Magento connection!!!"))
			else:
				instance_id = config_id[0]
		if instance_id:
			obj = self.browse(cr, uid, instance_id)
			url = obj.name + XMLRPC_API
			user = obj.user
			pwd = obj.pwd
			if obj.language:
				context['lang'] = obj.language
			try:
				server = xmlrpclib.Server(url)
				session = server.login(user, pwd)
			except xmlrpclib.Fault, e:
				raise osv.except_osv(_('Error, %s')%e.faultString, _("Invalid Login Credentials!!!"))
			except IOError, e:
				raise osv.except_osv(_('Error'), _(" %s")% e)
			except Exception,e:
				raise osv.except_osv(_('Error'), _("Magento Connection Error in connecting: %s") % e)
			if session:
				return [url, session, instance_id]
			else:
				return False
				
magento_configure()

	################### Catalog Mapping Models ########################
class magento_product_template(osv.osv):
	_name="magento.product.template"
	_order = 'id desc'
	_description = "Magento Product Template"
	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		vals['erp_template_id']=vals['template_name']
		if not vals.has_key('base_price'): 	
		# if float(vals['base_price'])<0.00000000000001:
			vals['base_price'] = self.pool.get('product.template').browse(cr,uid,vals['erp_template_id']).list_price
		return super(magento_product_template, self).create(cr, uid, vals, context=context)
	_columns = {		
		'template_name':fields.many2one('product.template', 'Template Name'),
		'erp_template_id':fields.integer('Odoo`s Template Id'),
		'mage_product_id':fields.integer('Magento`s Product Id'),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'base_price': fields.float('Base Price(excl. impact)'),
		'is_variants':fields.boolean('Is Variants'),
		'created_by':fields.char('Created By', size=64),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),		
		'need_sync': fields.selection([('Yes','Yes'),('No','No')],'Update Required'),
	}
	_defaults = {
		'created_by':'odoo',
		'need_sync':'No',
	}

	def create_n_update_attribute_line(self, cr, uid, data, context=None):
		line_dict = {}
		if context is None:
			context = {}
		# _logger.info("Attribute: %r", data)
		price_pool = self.pool.get('product.attribute.price')
		attribute_line = self.pool.get('product.attribute.line')
		if data.has_key('product_tmpl_id'):
			template_id = data.get('product_tmpl_id')
			attribute_id = data.get('attribute_id')
			if data.has_key('values') and data['values']:
				value_ids = []
				for value in data['values']:
					value_id = value['value_id']
					value_ids.append(value_id)
					if value['price_extra']:
						price_extra = value['price_extra']
						search_ids = price_pool.search(cr, uid, [('product_tmpl_id','=',template_id), ('value_id','=',value_id)])
						if search_ids:
							price_pool.write(cr, uid, search_ids[0], {'price_extra':price_extra})
						else:
							a = price_pool.create(cr, uid, {'product_tmpl_id':template_id,'value_id':value_id, 'price_extra':price_extra})
				line_dict['value_ids'] = [(6, 0, value_ids)]
			search = attribute_line.search(cr, uid, [('product_tmpl_id','=',template_id),('attribute_id','=',attribute_id)])
			if search:
				attribute_line.write(cr, uid, search[0], line_dict, context)
			else:
				line_dict['attribute_id'] = attribute_id
				line_dict['product_tmpl_id'] = template_id
				attr_line_id = attribute_line.create(cr, uid, line_dict, context)
			return True
		return False

magento_product_template()


class magento_product(osv.osv):			
	_name="magento.product"
	_order = 'id desc'
	_rec_name = "pro_name"
	_description = "Magento Product"
	_columns = {
		'pro_name':fields.many2one('product.product', 'Product Name'),
		'oe_product_id':fields.integer('Odoo Product Id'),
		'mag_product_id':fields.integer('Magento Product Id'),
		'need_sync':fields.selection([('Yes', 'Yes'),('No', 'No')],'Update Required'),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
	_defaults={
		'created_by':'odoo',
		'need_sync':'No',
	}
magento_product()


class magento_category(osv.osv):			
	_name = "magento.category"
	_order = 'id desc'
	_rec_name = "cat_name"
	_description = "Magento Category"

	_columns = {
		'cat_name':fields.many2one('product.category', 'Category Name'),
		'oe_category_id':fields.integer('Odoo Category Id'),
		'mag_category_id':fields.integer('Magento Category Id'),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'need_sync':fields.selection([('Yes', 'Yes'),('No', 'No')],'Update Required'),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
	_defaults={
		'created_by':'odoo',
		'need_sync':'No',
	}
	
	def create_category(self, cr, uid, data, context=None):
		"""Create and update a category by any webservice like xmlrpc.
		@param data: details of category fields in list.
		"""	
		if context is None:
			context = {}	
		categ_dic = {}		
		category_id = 0
		if data.has_key('name') and data['name']:
			categ_dic['name'] = _unescape(data.get('name'))
			
		if data.has_key('type'):
			categ_dic['type'] = data.get('type')
		if data.has_key('parent_id'):
			categ_dic['parent_id'] = data.get('parent_id')
		if data.get('method') == 'create':
			mage_category_id = data.get('mage_id')
			category_id = self.pool.get('product.category').create(cr, uid, categ_dic, context)
			self.create(cr, uid,{'cat_name':category_id,'oe_category_id':category_id,'mag_category_id':mage_category_id,'instance_id':context.get('instance_id'),'created_by':'Magento'})
			return category_id
		if data.get('method') == 'write':
			category_id = data.get('category_id')
			self.pool.get('product.category').write(cr, uid, category_id, categ_dic, context)
			return True
		return False
magento_category()

class magento_attribute_set(osv.osv):
	_name = "magento.attribute.set"
	_description = "Magento Attribute Set"
	_order = 'id desc'

	_columns = {
		'name':fields.char('Magento Attribute Set'),
		'attribute_ids':fields.many2many('product.attribute', 'product_attr_set','set_id','attribute_id','Product Attributes', readonly=True, help="Magento Set attributes will be handle only at magento."),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'set_id':fields.integer('Magento Set Id', readonly=True),
		'created_by':fields.char('Created By', size=64),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
	}
	_defaults={
		'created_by': 'odoo',
	}

	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		if context.has_key('instance_id'):
			vals['instance_id'] = context.get('instance_id')
		#vals['instance_id'] = context.get('instance_id')
		# self.create(cr,)
		return super(magento_attribute_set, self).create(cr, uid, vals, context=context)

magento_attribute_set()

class magento_product_attribute(osv.osv):
	_name = "magento.product.attribute"
	_order = 'id desc'
	_description = "Magento Product Attribute"


	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		vals['erp_id'] = vals['name']
		if context.has_key('instance_id'):
			vals['instance_id'] = context.get('instance_id')
		return super(magento_product_attribute, self).create(cr, uid, vals, context=context)
	
	def write(self,cr,uid,ids,vals,context=None):
		if context is None:
			context = {}
		if vals.has_key('name'):
			vals['erp_id']=vals['name']
		if context.has_key('instance_id'):
			vals['instance_id'] = context.get('instance_id')	
		return super(magento_product_attribute,self).write(cr,uid,ids,vals,context=context)
	
	_columns = {
		'name':fields.many2one('product.attribute', 'Product Attribute'),
		'erp_id':fields.integer('Odoo`s Attribute Id'),	
		'mage_id':fields.integer('Magento`s Attribute Id'),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'created_by':fields.char('Created By', size=64),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
	}
	_defaults={
		'created_by': 'odoo',
	}
magento_product_attribute()

class magento_product_attribute_value(osv.osv):			
	_name="magento.product.attribute.value"
	_order = 'id desc'
	_description = "Magento Product Attribute Value"
	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		vals['erp_id'] = vals['name']
		if context.has_key('instance_id'):
			vals['instance_id'] = context.get('instance_id')	
		return super(magento_product_attribute_value, self).create(cr, uid, vals, context=context)
	
	def write(self,cr,uid,ids,vals,context=None):
		if context is None:
			context = {}
		if vals.has_key('name'):
			vals['erp_id'] = vals['name']
		if context.has_key('instance_id'):
			vals['instance_id'] = context.get('instance_id')
		return super(magento_product_attribute_value,self).write(cr,uid,ids,vals,context=context)
		
	_columns = {
		'name':fields.many2one('product.attribute.value', 'Attribute Value'),
		'erp_id':fields.integer('Odoo Attribute Value Id'),	
		'mage_id':fields.integer('Magento Attribute Value Id'),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'created_by':fields.char('Created By', size=64),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
	}
	_defaults={
		'created_by': 'odoo',
	}
magento_product_attribute_value()

	################### Catalog Mapping Models End ########################

	############## Magento Customer Mapping Models ################
class magento_customers(osv.osv):			
	_name="magento.customers"
	_order = 'id desc'
	_rec_name = "cus_name"
	_description = "Magento Customers"
	_columns = {		
		'cus_name':fields.many2one('res.partner', 'Customer Name'),		
		'oe_customer_id':fields.integer('Odoo Customer Id'),
		'mag_customer_id':fields.char('Magento Customer Id',size=50),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'mag_address_id':fields.char('Magento Address Id',size=50),
		'need_sync':fields.selection([('Yes', 'Yes'),('No', 'No')],'Update Required'),
		'created_by':fields.char('Created By', size=64),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
	}
	_defaults={
		'created_by': 'odoo',
		'need_sync': 'No',
	}

	def create_customer(self, cr, uid, data, context=None):
		"""Create a customer by any webservice like xmlrpc.
		@param data: details of customer fields in list.
		@param context: A standard dictionary
		@return: Odoo Customer id
		"""		
		cus_dic = {}
		dic = {}
		customer_id = 0
		if data.has_key('country_code'):
			country_ids = self.pool.get('res.country').search(cr, uid,[('code','=',data.get('country_code'))])
			if country_ids:
				cus_dic['country_id'] = country_ids[0]
				if data.has_key('region') and data['region']:
					region = _unescape(data.get('region'))
					state_ids = self.pool.get('res.country.state').search(cr, uid,[('name', '=', region)])
					if state_ids:
						cus_dic['state_id'] = state_ids[0]
					else:
						dic['name'] = region
						dic['country_id'] = country_ids[0]
						dic['code'] = region[:2].upper()
						state_id = self.pool.get('res.country.state').create(cr, uid,dic)
						cus_dic['state_id'] = state_id
		if data.has_key('is_company'):
			cus_dic['is_company'] = data.get('is_company')
		if data.has_key('use_parent_address'):
			cus_dic['use_parent_address'] = data.get('use_parent_address')
		if data.has_key('parent_id'):
			cus_dic['parent_id'] = data.get('parent_id')
		if data.has_key('customer'):
			cus_dic['customer'] = data.get('customer')
		if data.has_key('address'):
			cus_dic['wk_address'] = data.get('address')
		if data.has_key('wk_company'):
			cus_dic['wk_company'] = _unescape(data.get('wk_company'))
		if data.has_key('partner_id'):
			customer_id = data.get('partner_id')
		if data.has_key('name') and data['name']:
			cus_dic['name'] = _unescape(data.get('name'))
		if data.has_key('email') and  data['email']:
			cus_dic['email'] = _unescape(data.get('email'))
		if data.has_key('street') and data['street']:
			cus_dic['street'] = _unescape(data.get('street'))
		if data.has_key('street2') and data['street2']:
			cus_dic['street2'] = _unescape(data.get('street2'))
		if data.has_key('city') and data['city']:
			cus_dic['city'] = _unescape(data.get('city'))
		if data.has_key('vat') and data['vat']:
			cus_dic['vat'] = data.get('vat')
		cus_dic['type'] = data.get('type',False)
		cus_dic['zip'] = data.get('zip',False)
		cus_dic['phone'] = data.get('phone',False)
		cus_dic['fax'] = data.get('fax',False)
		cus_dic['lang'] = data.get('lang',False)
		if data.has_key('tag') and data["tag"]:
			tag = _unescape(data.get('tag'))
			tag_ids = self.pool.get('res.partner.category').search(cr,uid,[('name','=',tag)], limit=1)
			if not tag_ids:
				tag_id = self.pool.get('res.partner.category').create(cr,uid,{'name':tag})
			else:
				tag_id = tag_ids[0]
			cus_dic['category_id'] = [(6,0,[tag_id])]
		if data.get('method') == 'create':
			customer_id = self.pool.get('res.partner').create(cr, uid, cus_dic, context)
			return customer_id
		if data.get('method') == 'write':
			self.pool.get('res.partner').write(cr, uid, customer_id, cus_dic, context)
			return customer_id
		return False
magento_customers()


class magento_region(osv.osv):			
	_name="magento.region"
	_order = 'id desc'
	_description = "Magento Region"	
	_columns = {
		'name': fields.char('Region Name',size=100),
		'mag_region_id':fields.integer('Magento Region Id'),		
		'country_code': fields.char('Country Code',size=10),			
		'region_code': fields.char('Region Code',size=10),
		'created_by':fields.char('Created By', size=64),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
	}
	_defaults={
		'created_by': 'odoo'
	}
magento_region()
	############# Customer Model End #############################

ORDER_STATUS = [
		('draft', 'Draft Quotation'),
		('sent', 'Quotation Sent'),
		('cancel', 'Cancelled'),
		('waiting_date', 'Waiting Schedule'),
		('progress', 'Sales Order'),
		('manual', 'Sale to Invoice'),
		('shipping_except', 'Shipping Exception'),
		('invoice_except', 'Invoice Exception'),
		('done', 'Done'),
]

class magento_orders(osv.osv):
	_name="magento.orders"
	_order = 'id desc'
	_rec_name = "order_ref"
	_description = "Magento Orders"
	_columns = {
		'order_ref':fields.many2one('sale.order', 'Order Reference'),
		'oe_order_id':fields.integer('Odoo order Id'),
		'mage_increment_id':fields.char('Magento order Id', size=100),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'order_status': fields.related('order_ref', 'state', type='selection', selection=ORDER_STATUS, string='Order Status'),
		'paid_status': fields.related('order_ref', 'invoiced', type='boolean', relation='sale.order', string='Paid'),
		'ship_status': fields.related('order_ref', 'shipped', type='boolean', relation='sale.order', string='Shipped'),
		'order_total': fields.related('order_ref', 'amount_total', type='float', relation='sale.order', string='Order Total'),
		'create_date':fields.datetime('Created Date'),
	}

	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}		
		if context.has_key('instance_id'):
			vals['instance_id'] = context.get('instance_id')	
		return super(magento_orders, self).create(cr, uid, vals, context=context)
magento_orders()

	###############     History 	####################
	

class magento_sync_history(osv.osv):
	_name ="magento.sync.history"
	_order = 'id desc'
	_description = "Magento Synchronization History"
	_columns = {
		'status': fields.selection((('yes','Successfull'),('no','Un-Successfull')),'Status'),	
		'action_on': fields.selection((('product','Product'),('category','Category'),('customer','Customer'),('order','Order')),'Action On'),
		'action': fields.selection((('a','Import'),('b','Export'),('c','Update')),'Action'),
		'create_date': fields.datetime('Created Date'),
		'error_message': fields.text('Summary'),
	}
magento_sync_history()
# END