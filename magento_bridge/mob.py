 # -*- coding: utf-8 -*-
##############################################################################
#		
#    Odoo, Open Source Management Solution
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
from decimal import *
import re
import xmlrpclib
import openerp.tools
import urllib
import datetime
from openerp import workflow
from openerp import SUPERUSER_ID, api
from ..base.res.res_partner import _lang_get


class magento_configure(osv.osv):
	_name = "magento.configure"
	_inherit = ['mail.thread']
	_description = "Magento Configuration"
	def create(self, cr, uid, vals, context=None):
		active_ids = self.pool.get('magento.configure').search(cr, uid, [('active','=',True)])		
		if vals['active']:
			if active_ids:
				raise osv.except_osv(_('Warning'), _("Sorry, Only one active connection is allowed."))
		return super(magento_configure, self).create(cr, uid, vals, context=context)
		
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

	_columns = {
		'name': fields.char('Base URL', required=True, size=255 ,select=True),
		'user':fields.char('API User Name', required=True, size=100),
		'pwd':fields.char('API Password',required=True, size=100),
		'status':fields.char('Connection Status',readonly=True, size=255),
		'active':fields.boolean('Active'),
		'credential':fields.boolean('Show/Hide Credentials Tab', help="If Enable, Credentials tab will be displayed, And after filling the details you can hide the Tab."),
		'auto_invoice':fields.boolean('Auto Invoice',help='If Enabled, Order will automatically Invoiced on Magento when Odoo order Get invoiced.'),
		'auto_ship':fields.boolean('Auto Shipment', help='If Enabled, Order will automatically shipped on Magento when Odoo order Get Delivered.' ),
		'create_date':fields.datetime('Created Date'),
		'language':fields.selection(_lang_get, "Default Language", required=True, help="Selected language is loaded in the system, all documents related to this contact will be synched in this language."),
		'category':fields.many2one('product.category', "Default Category", required=True, help="Selected Category will be set default category for odoo's product, in case when magento product doesn\'t belongs to any catgeory."),
		'state':fields.selection([('enable','Enable'),('disable','Disable')],'Status', help="status will be consider during order invoice, order delivery and order cancel, to stop asynchronous process at other end.", size=100),
		'inventory_sync':fields.selection([('enable','Enable'),('disable','Disable')],'Product Inventory Sync', help="If enable, product inventory will sync during product sync/updates else it won't sync.", size=100, required=True),
	}
	_defaults = {
		'active':lambda *a: 1,	
		'auto_ship':lambda *a: 1,
		'auto_invoice':lambda *a: 1,
		'credential':lambda *a: 1,
		'language': api.model(lambda self: self.env.lang),
		'category':_default_category,
		'state':'enable',
		'inventory_sync':'enable',
	}
	
	def write(self, cr, uid, ids, vals, context=None):
		active_ids=self.pool.get('magento.configure').search(cr, uid, [('active','=',True)])		
		if vals:
			if len(active_ids)>0 and vals.has_key('active') and vals['active']:
				raise osv.except_osv(_('Warning'), _("Sorry, Only one active connection is allowed."))
		return super(magento_configure, self).write(cr, uid, ids, vals, context=context)
	
	#############################################
	##    		magento connection		   	   ##
	#############################################
	def test_connection(self, cr, uid, ids, context=None):
		text = 'test connection Un-successful please check the magento api credentials!!!'
		status = 'Magento Connection Un-successful'		
		obj = self.browse(cr,uid,ids[0])
		url = obj.name+'/index.php/api/xmlrpc'
		user = obj.user
		pwd = obj.pwd
		session = 0
		try:
			server = xmlrpclib.Server(url)
			session = server.login(user,pwd)
		except xmlrpclib.Fault, e:
			text = "Error, %s Invalid Login Credentials!!!"%(e.faultString)
		except IOError, e:
			text = str(e)
		except Exception,e:
			text = "Magento Connection Error in connecting: %s"%(e)
		if session:
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
		config_id = self.search(cr,uid,[('active','=',True)])
		if len(config_id) > 1:
			raise osv.except_osv(_('Error'), _("Sorry, only one Active Configuration setting is allowed."))
		if not config_id:
			raise osv.except_osv(_('Error'), _("Please create the configuration part for Magento connection!!!"))
		else:
			obj = self.browse(cr,uid,config_id[0])
			url = obj.name+'/index.php/api/xmlrpc'
			user = obj.user
			pwd = obj.pwd
			if obj.language:				
				context['lang'] = obj.language
			try:
				server = xmlrpclib.Server(url)
				session = server.login(user,pwd)
			except xmlrpclib.Fault, e:
				raise osv.except_osv(_('Error, %s')%e.faultString, _("Invalid Login Credentials!!!"))
			except IOError, e:
				raise osv.except_osv(_('Error'), _(" %s")% e)
			except Exception,e:
				raise osv.except_osv(_('Error'), _("Magento Connection Error in connecting: %s") % e)
			if session:
				return [url,session]
			else:
				return False
				
magento_configure()

class magento_synchronization(osv.osv):
	_name = "magento.synchronization"
	_description = "Magento Synchronization"	


	def open_configuration(self, cr, uid, ids, context=None):
		view_id = False
		setting_ids = self.pool.get('magento.configure').search(cr, uid, [('active','=',True)])
		if  setting_ids:
			view_id = setting_ids[0]
		return {
				'type': 'ir.actions.act_window',
				'name': 'Configure Magento Api',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'magento.configure',
				'res_id': view_id,
				'target': 'current',
				'domain': '[]',
			}

	def sync_template_attribute_set(self, cr, uid, ids, context=None):
		temp_pool = self.pool.get('product.template')
		mage_set_pool = self.pool.get('magento.attribute.set')
		template_ids = temp_pool.search(cr, uid, [])
		success_ids = []
		fails_ids = []
		for temp_id in template_ids:
			attribute_line_ids = temp_pool.browse(cr, uid, temp_id).attribute_line_ids
			attributes = []
			set_search1 = []
			default_search = mage_set_pool.search(cr, uid,[])
			if default_search:
				default_set = default_search[0]
			if attribute_line_ids:
				for attr in attribute_line_ids:
					set_search2 = []
					set_search2 = mage_set_pool.search(cr, uid, [('attribute_ids','=',attr.attribute_id.id)])
					if not set_search2:
						set_search1 = []
						break
					if not set_search1 :
						set_search1 = set_search2
					else:
						set_search1 = list(set(set_search1) & set(set_search2))
				if set_search1:
					temp_pool.write(cr, uid, temp_id, {'attribute_set_id':set_search1[0]})			
					success_ids.append(temp_id)
				else:
					fails_ids.append(temp_id)
			else:
				temp_pool.write(cr, uid, temp_id, {'attribute_set_id':default_set})
		if success_ids:
			msg = 'Magento attribute set synchronized successfully at Product Template(s) ids %s.'%success_ids
		if fails_ids:
			msg += '\nNo matched magento attribute set found for product template(s) ids %s.'%fails_ids
		partial = self.pool.get('message.wizard').create(cr, uid, {'text':msg})
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


	########## update specific category ##########
	def _update_specific_category(self, cr, uid, id, url, session, context):
		get_category_data = {}
		cat_up = False
		cat_mv = False
		cat_pool = self.pool.get('magento.category')
		cat_obj = cat_pool.browse(cr,uid,id)
		cat_id = cat_obj.oe_category_id
		mage_id = cat_obj.mag_category_id
		mag_parent_id=1
		if cat_id and mage_id:
			obj_cat = self.pool.get('product.category').browse(cr, uid, cat_id, context)
			get_category_data['name'] = obj_cat.name
			get_category_data['available_sort_by'] = 1
			get_category_data['default_sort_by'] = 1
			parent_id = obj_cat.parent_id.id or False
			if parent_id:
				search = cat_pool.search(cr,uid,[('cat_name','=',parent_id)])
				if search:
					mag_parent_id = cat_pool.browse(cr, uid, search[0], context=context).mag_category_id or 1
				else :
					mag_parent_id = self.sync_categories(cr, uid, url, session, parent_id, context)
			update_data = [mage_id, get_category_data]
			move_data = [mage_id,mag_parent_id]
			try:
				server = xmlrpclib.Server(url)
				cat = server.call(session, 'catalog_category.update', update_data)
				cat_mv = server.call(session, 'catalog_category.move', move_data)
				self.pool.get('magento.category').write(cr, uid, id, {'need_sync':'No'})
			except xmlrpclib.Fault, e:
				return [0, str(e)]
			except Exception, e:
				return [0, str(e)]
			return  [1, cat_id]

	def update_categories(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		text = text1 = ''
		up_error_ids = []
		success_ids =[]
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]
			server = xmlrpclib.Server(url)
			map_id = self.pool.get('magento.category').search(cr,uid,[('need_sync','=','Yes'),('mag_category_id','!=',-1)])
			if not map_id:
				raise osv.except_osv(_('Information'), _("No category(s) has been found to be Update on Magento!!!"))
			if map_id:
				for i in map_id:
					cat_update = self._update_specific_category(cr, uid, i, url, session, context)
					if cat_update:
						if cat_update[0] != 0:
							success_ids.append(cat_update[1])
						else:
							up_error_ids.append(cat_update[1])
				if success_ids:
					text = 'List of %s Category ids has been sucessfully updated to Magento. \n'%success_ids
					self.pool.get('magento.sync.history').create(cr,uid,{'status':'yes','action_on':'category','action':'c','error_message':text})
				if up_error_ids:
					text1 = 'The Listed Category ids %s does not updated on Magento.'%up_error_ids	
					self.pool.get('magento.sync.history').create(cr,uid,{'status':'no','action_on':'category','action':'c','error_message':text1})
				partial = self.pool.get('message.wizard').create(cr, uid, {'text':text+text1})
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

	def create_category(self, cr, uid, url, session, catg_id, parent_id, catgname):					
		mage_cat = parent_id
		server = xmlrpclib.Server(url)
		catgdetail = dict({
			'name':catgname,
			'is_active':1,			
			'available_sort_by':1,
			'default_sort_by' : 1,			
			'is_anchor' : 1,
			'include_in_menu' : 1
		})    
		if catg_id > 0:
			updatecatg = [parent_id,catgdetail]	
			try:
				mage_cat = server.call(session, 'catalog_category.create', updatecatg)				
			except xmlrpclib.Fault, e:				
				return 0
		else:
			return False
		if mage_cat > 0:
			self.pool.get('magento.category').create(cr, uid, {'cat_name':catg_id,'oe_category_id':catg_id,'mag_category_id':mage_cat, 'created_by':'Odoo'})
			# Magento mapping Entry				
			server.call(session, 'magerpsync.category_map', [{'name':catgname,'mage_category_id':mage_cat,'erp_category_id':catg_id,'created_by':'Odoo'}])
			return mage_cat
	
	def sync_categories(self, cr, uid, url, session, cat_id, context):
		check = self.pool.get('magento.category').search(cr, uid, [('oe_category_id','=',cat_id)], context=context)
		if not check:
			obj_catg = self.pool.get('product.category').browse(cr,uid,cat_id, context)
			name = obj_catg.name
			if obj_catg.parent_id.id:
				p_cat_id = self.sync_categories(cr, uid, url, session, obj_catg.parent_id.id, context)
			else:
				p_cat_id = self.create_category(cr, uid, url, session, cat_id, 1, name)
				return p_cat_id
			category_id = self.create_category(cr, uid, url, session, cat_id, p_cat_id, name)
			return category_id
		else:
			mage_id = self.pool.get('magento.category').browse(cr, uid, check[0]).mag_category_id
			return mage_id
			
	#############################################
	##    		Export All Categories  	   	   ##
	#############################################
	
	def export_categories(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		catg_map = {}
		map_dic =[]
		length = 0
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)			
		if connection:
			mage_cat_pool = self.pool.get('magento.category')
			url = connection[0]
			session = connection[1]
			map_id = mage_cat_pool.search(cr,uid,[])
			for m in map_id:
				map_obj = mage_cat_pool.browse(cr,uid,m)				
				map_dic.append(map_obj.oe_category_id)
				catg_map[map_obj.oe_category_id] = map_obj.mag_category_id

			erp_catg = self.pool.get('product.category').search(cr,uid,[('name','!=','All products'),('id','not in',map_dic)], context = context)
			if not erp_catg:
				raise osv.except_osv(_('Information'), _("All category(s) has been already exported on magento."))
				
			for l in erp_catg:
				cat_id = self.sync_categories(cr, uid, url, session, l, context)
				length += 1
			text="%s category(s) has been Exported to magento."%(length)
			self.pool.get('magento.sync.history').create(cr,uid,{'status':'yes','action_on':'category','action':'b','error_message':text})
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
	
	#############################################
	##    export bulk/selected category  	   ##
	#############################################
	
	def export_bulk_category(self, cr, uid, context=None):
		if context is None:
			context = {}
		text =  ''
		text1 = text2= ''
		fail_ids= []
		error_ids=[]
		up_error_ids =[]
		success_up_ids=[]
		success_exp_ids= []
		bulk_ids = context.get('active_ids')	
		map_pool = self.pool.get('magento.category')
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]			
			for l in bulk_ids:
				search = map_pool.search(cr,uid,[('cat_name','=',l)])
				if not search:
					cat_id = self.sync_categories(cr, uid, url, session, l, context)
					if cat_id:
						success_exp_ids.append(l)
				else :
					map_id = map_pool.browse(cr,uid,search[0])
					if map_id.need_sync == 'Yes' and map_id.mag_category_id != -1:
						cat_update = self._update_specific_category(cr, uid,  map_id.id, url, session, context)
						if cat_update:
							if cat_update[0] != 0:
								success_up_ids.append(l)
							else:
								up_error_ids.append(cat_update[1])
					else:
						fail_ids.append(l)
			if success_exp_ids:
				text = "\nThe Listed category ids %s has been created on magento."%(success_exp_ids)
			if fail_ids:
				text += "\nSelected category ids %s are already synchronized on magento."%(fail_ids)
			if text:
				self.pool.get('magento.sync.history').create(cr,uid,{'status':'yes','action_on':'product','action':'b','error_message':text})
			if success_up_ids:
				text1 = '\nThe Listed category ids %s has been successfully updated to Magento. \n'%success_up_ids
				self.pool.get('magento.sync.history').create(cr,uid,{'status':'yes','action_on':'product','action':'c','error_message':text1})
			if up_error_ids:
				text2 = '\nThe Listed category ids %s does not updated on magento.'%up_error_ids
				self.pool.get('magento.sync.history').create(cr,uid,{'status':'no','action_on':'product','action':'c','error_message':text2})
			partial = self.pool.get('message.wizard').create(cr, uid, {'text':text+text1+text2})
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

	#############################################
	## 	 Export Diamension and values          ##
	#############################################
	def export_attributes_and_their_values(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		map_dic = []		
		map_dict = {}	
		att_type = 0
		value = 0
		error_message = ''
		status = 'yes'
		up_error_ids = []
		success_ids =[]
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]
			server = xmlrpclib.Server(url)
			# vals = server.call(session, 'product_attribute.list',[4])
			magento_pro_attr_pool = self.pool.get('magento.product.attribute')
			product_attr_pool = self.pool.get('product.attribute')
			magento_pro_attr_val = self.pool.get('magento.product.attribute.value')
			product_attr_val = self.pool.get('product.attribute.value')
			map_id = magento_pro_attr_pool.search(cr,uid,[])
			for m in map_id:
				map_obj = magento_pro_attr_pool.browse(cr,uid,m)				
				map_dic.append(map_obj.erp_id)
				map_dict.update({map_obj.erp_id:map_obj.mage_id})
			erp_pro = product_attr_pool.search(cr, uid, [], context=context)
			if erp_pro:
				for type_id in erp_pro:
					obj_pro_attr = product_attr_pool.browse(cr, uid, type_id, context)
					if type_id not in map_dic:
						name = obj_pro_attr.name
						label = obj_pro_attr.name
						# position = obj_pro_attr.sequence
						create_dim_type = self.create_product_attribute(cr, uid, url, session, type_id, name, label)
						att_type+=1
					else:
						mage_id = map_dict.get(type_id)
						create_dim_type = [int(mage_id)]
					if create_dim_type[0]==0:
						status='no'
						error_message=error_message + create_dim_type[1]
					else:
						mage_id = create_dim_type[0]
						for value_id in obj_pro_attr.value_ids:
							if not magento_pro_attr_val.search(cr,uid,[('erp_id','=',value_id.id)]):
								obj_attr_val = product_attr_val.browse(cr, uid, value_id.id, context)
								name = obj_attr_val.name
								position = obj_attr_val.sequence
								create_attr_val = self.create_attribute_value(cr, uid, url, session, mage_id, value_id.id, name, position)
								if create_attr_val[0]==0:
									status='no'
									error_message = error_message + create_attr_val[1]
								else:
									value+=1
			if status=='yes':
				error_message+=" %s Product Attribute(s) and their %s value(s) has been created. "%(att_type,value)
			if not erp_pro:
				error_message="No new Product Attribute(s) found !!!"
			partial = self.pool.get('message.wizard').create(cr, uid, {'text':error_message})
			return { 'name':_("Message"),
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

	def sync_attribute_set(self, cr, uid, data):
		set_pool = self.pool.get('magento.attribute.set')
		erp_set_id = 0
		set_dic = {}
		res = False
		if data.has_key('name') and data.get('name'):
			search_ids = set_pool.search(cr, uid, [('name','=',data.get('name'))])
			if not search_ids:
				set_dic['name'] = data.get('name')
				if data.has_key('set_id') and data.get('set_id'):
					set_dic['set_id'] = data.get('set_id')
				set_dic['created_by'] = 'Magento'
				erp_set_id = set_pool.create(cr, uid, set_dic)
			else:
				erp_set_id = search_ids[0]
			if erp_set_id: 
				if data.has_key('set_id') and data.get('set_id'):
					dic = {}
					dic['set_id'] = data.get('set_id')
					if data.has_key('attribute_ids') and data.get('attribute_ids'):
						dic['attribute_ids'] = [(6, 0, data.get('attribute_ids'))]
					else:
						dic['attribute_ids'] = [[5]]
					res = set_pool.write(cr, uid, erp_set_id, dic)
		return res

	def create_product_attribute(self, cr, uid, url, session, erp_pro_attr_id, name, label, position='0', context=None):
		if context is None:
			context = {}
		name = name.lower().replace(" ","_").replace("-","_")
		if session:
			server = xmlrpclib.Server(url)
			attrribute_data = {
					'attribute_code':name,
					'scope':'global',
					'frontend_input':'select',
					'is_configurable':1,
					'is_required':1,
					'frontend_label':[{'store_id':0,'label':label}]
				}
			try:
				a_id = server.call(session, 'product_attribute.create', [attrribute_data])
				currset = server.call(session, 'product_attribute_set.list')
				# currsetid = currset[0].get('set_id')
				currsetname = currset[0].get('name')
				# server.call(session, 'product_attribute_set.attributeAdd', [a_id,currsetid])
			except xmlrpclib.Fault, e:
				return [0,' Error in creating Attribute Type(ID: %s).%s'%(str(erp_pro_attr_id),str(e))]
			if a_id:
				self.pool.get('magento.product.attribute').create(cr, uid, {'name':erp_pro_attr_id, 'erp_id':erp_pro_attr_id, 'mage_id':a_id, 'mage_attribute_set_name':currsetname , 'created_by':'Odoo'})
				server.call(session, 'magerpsync.attribute_map', [{'name':name, 'mage_attribute_id':a_id, 'erp_dimension_type_id':erp_pro_attr_id, 'mage_attribute_set_name':currsetname, 'created_by':'Odoo'}])
				# self.sync_attribute_set(cr, uid, {'name':currsetname, 'attribute_id':erp_pro_attr_id, 'set_id':currsetid})
				return [a_id,'']

	def create_attribute_value(self, cr, uid ,url, session, mage_attr_id, erp_attr_val, name, position='0' ,context=None):
		if context is None:
			context = {}
		if session:
			server = xmlrpclib.Server(url)
			options_data = {
						'label':[{'store_id':0,'value':name}],
						'order':position,
						'is_default':0
					}
			try:
				o_id = server.call(session, 'product_attribute.addOption', [mage_attr_id,options_data])
			except xmlrpclib.Fault, e:
				return [0,' Error in creating Attribute Option(ID: %s).%s'%(str(erp_attr_val),str(e))]
			if o_id:
				self.pool.get('magento.product.attribute.value').create(cr, uid, {'name':erp_attr_val, 'erp_id':erp_attr_val, 'mage_id':o_id, 'created_by':'Odoo'})
				server.call(session, 'magerpsync.attributeoption_map', [{'name':name, 'mage_attribute_option_id':o_id, 'erp_dimension_option_id':erp_attr_val, 'created_by':'Odoo'}])
				return [o_id,'']
	####################################################
	## check for attributes belongs to same attribute ##
	####################################################
	def check_attribute_set(self, cr, uid):
		template_ids = self.pool.get('product.template').search(cr, uid, [('attribute_line_ids','!=', False)])
		
		setname = ''
		for attr in attribute_line_ids:
			search_id = self.pool.get('magento.product.attribute').search(cr, uid,[('name','=',attr.attribute_id.id)])
			if search_id :
				if not setname:
					setname = self.pool.get('magento.product.attribute').browse(cr, uid, search_id[0]).mage_attribute_set_name
				else:
					tempsetname = self.pool.get('magento.product.attribute').browse(cr, uid, search_id[0]).mage_attribute_set_name
					if setname != tempsetname:
						self.pool.get('magento.sync.history').create(cr,uid,{'status':'no','action_on':'product','action':'b','error_message':'product attributes must belongs to same attribute set'})
						return 0
			else:
				self.pool.get('magento.sync.history').create(cr,uid,{'status':'no','action_on':'product','action':'b','error_message':'product attributes not synchronized to magento'})
				return 0
		return 1

	#############################################
	##    	update specific product template   ##
	#############################################
	def _update_specific_product_template(self, cr, uid, id, url, session, context):
		server = xmlrpclib.Server(url)
		get_product_data = {}
		mage_variant_ids=[]
		mage_price_changes = {}
		map_tmpl_pool = self.pool.get('magento.product.template')
		attr_price_pool = self.pool.get('product.attribute.price')
		temp_obj = map_tmpl_pool.browse(cr, uid, id)
		temp_id = temp_obj.erp_template_id
		mage_id = temp_obj.mage_product_id
		if temp_id and mage_id:
			map_prod_pool = self.pool.get('magento.product')
			prod_catg = []
			obj_pro = self.pool.get('product.template').browse(cr, uid, temp_id, context)
			for j in obj_pro.categ_ids:
				mage_categ_id = self.sync_categories(cr, uid, url, session, j.id, context)
				prod_catg.append(mage_categ_id)
			if obj_pro.categ_id.id:
				mage_categ_id = self.sync_categories(cr, uid, url, session, obj_pro.categ_id.id, context)
				prod_catg.append(mage_categ_id)
			get_product_data['name'] = obj_pro.name
			get_product_data['price'] = obj_pro.list_price or 0.00
			get_product_data['weight'] = obj_pro.weight_net or 0.00
			get_product_data['categories'] = prod_catg		
			if obj_pro.product_variant_ids:
				if temp_obj.is_variants == True and obj_pro.is_product_variant == False:
					if obj_pro.attribute_line_ids :
						for obj in obj_pro.product_variant_ids:
							mage_update_ids = []
							vid = obj.id
							search_ids = map_prod_pool.search(cr, uid, [('oe_product_id','=',vid),('need_sync','=','Yes')])
							if search_ids:
								map_obj = map_prod_pool.browse(cr, uid, search_ids[0])
								mage_update_ids = self._update_specific_product(cr, uid, search_ids[0], url, session, context)
				else:
					for obj in obj_pro.product_variant_ids:
						name  = obj_pro.name
						price = obj_pro.list_price or 0.0
						mage_update_ids = []
						vid = obj.id
						search_ids = map_prod_pool.search(cr, uid, [('oe_product_id','=',vid),('need_sync','=','Yes')])
						if search_ids:
							map_obj = map_prod_pool.browse(cr, uid, search_ids[0])
							mage_update_ids = self._update_specific_product(cr, uid, search_ids[0], url, session, context=context)			
						if mage_update_ids and mage_update_ids[0]>0:
							map_tmpl_pool.write(cr, uid, id, {'need_sync':'No'})
						return mage_update_ids
			else:
				return [-1, str(id)+' No Variant Ids Found!!!']
			update_data = [mage_id, get_product_data]
			try:
				temp = server.call(session, 'product.update', update_data)
				map_tmpl_pool.write(cr, uid, id, {'need_sync':'No'})
			except xmlrpclib.Fault, e:
				return [0, str(temp_id)+str(e)]
			return [1, temp_id]

	def _search_single_values(self, cr, uid, temp_id, attr_id, context):
		dic = {}
		attr_line_pool = self.pool.get('product.attribute.line')
		search_ids  = attr_line_pool.search(cr, uid, [('product_tmpl_id','=',temp_id),('attribute_id','=',attr_id)], context=context)		
		if search_ids and len(search_ids) == 1:
			att_line_obj = attr_line_pool.browse(cr, uid, search_ids[0], context=context)
			if len(att_line_obj.value_ids) == 1:
				dic[att_line_obj.attribute_id.name] = att_line_obj.value_ids.name
		return dic


	############# check attributes lines and set attributes are same ########
	def _check_attribute_with_set(self, cr, uid, set_id, attribute_line_ids):
		set_attr_ids = self.pool.get('magento.attribute.set').browse(cr, uid, set_id).attribute_ids
		if not set_attr_ids:
			return [-1, str(id)+' Attribute Set Name has no attributes!!!']
		set_attr_list = list(set_attr_ids.ids)
		for attr_id in attribute_line_ids:	
			if attr_id.attribute_id.id not in set_attr_list:
				return [-1, str(id)+' Attribute Set Name not matched with attributes!!!']
		return [1]

	############# check attributes syned return mage attribute ids ########
	def _check_attribute_sync(self, cr, uid, type_obj):
		map_attr_pool = self.pool.get('magento.product.attribute')
		mage_attribute_ids = []
		type_search = map_attr_pool.search(cr, uid, [('name','=',type_obj.attribute_id.id)])
		if type_search:
			map_type_obj = map_attr_pool.browse(cr, uid, type_search[0])
			mage_attr_id = map_type_obj.mage_id
			mage_attribute_ids.append(mage_attr_id)
		return mage_attribute_ids		


	#############################################
	##    		Specific template sync	       ##
	#############################################
	def _export_specific_template(self, cr, uid, id, url, session, context):
		"""
		@param code: product Id.
		@param context: A standard dictionary
		@return: list
		"""
		prod_catg = []
		mage_product_id = 0
		mage_variant_ids = []
		get_product_data = {}
		mage_price_changes = {}
		mage_attribute_ids = []
		mage_attribute_set_name = ''		
		server = xmlrpclib.Server(url)
		if id:
			map_tmpl_pool = self.pool.get('magento.product.template') 
			map_prod_pool = self.pool.get('magento.product') 
			map_attr_pool = self.pool.get('magento.product.attribute')
			val_price_pool = self.pool.get('product.attribute.price')
			obj_pro = self.pool.get('product.template').browse(cr, uid, id, context)			
			for i in obj_pro.categ_ids:
				mage_categ_id = self.sync_categories(cr, uid, url, session, i.id, context)
				prod_catg.append(mage_categ_id)
			if obj_pro.categ_id.id:
				mage_categ_id = self.sync_categories(cr, uid, url, session, obj_pro.categ_id.id, context)
				prod_catg.append(mage_categ_id)
			template_sku = obj_pro.default_code or 'Template Ref %s'%id			
			if obj_pro.product_variant_ids:				
				if obj_pro.attribute_line_ids:
					set_id = obj_pro.attribute_set_id.id	
					############# check attributes lines and set attributes are same ########
					check_attribute = self._check_attribute_with_set(cr, uid, set_id, obj_pro.attribute_line_ids)
					if check_attribute and check_attribute[0] == -1:
						return check_attribute
					mage_set_id = obj_pro.attribute_set_id.set_id
					if mage_set_id:
						for type_obj in obj_pro.attribute_line_ids:
							############# check attributes syned ########
							mage_attr_ids = self._check_attribute_sync(cr, uid, type_obj)		
							if not mage_attr_ids:
								return [-1, str(id)+' Attribute not syned at magento!!!']
							mage_attribute_ids.append(mage_attr_ids[0])
							get_product_data['configurable_attributes'] = mage_attribute_ids
							single_value_dic = {}
							# fetching options values array for configurable product				
							for attr_id in obj_pro.attribute_line_ids:			
								attrname = attr_id.attribute_id.name.lower().replace(" ","_").replace("-","_")	
								val_dic = self._search_single_values(cr, uid, id, attr_id.attribute_id.id, context)
								if val_dic:
									single_value_dic.update(val_dic)						
								for value_id in attr_id.value_ids:	
									price_extra = 0.0
									##### product template and value extra price ##### 
									price_search = val_price_pool.search(cr, uid, [('product_tmpl_id','=',id),('value_id','=',value_id.id)])
									if price_search:
										price_extra = val_price_pool.browse(cr, uid, price_search[0]).price_extra
									valuename = value_id.name
									if mage_price_changes.has_key(attrname):
										mage_price_changes[attrname].update({valuename:price_extra})
									else:
										mage_price_changes[attrname] = {valuename:price_extra}
						
						for obj in obj_pro.product_variant_ids:
							vid = obj.id
							search_ids = map_prod_pool.search(cr, uid, [('oe_product_id','=',vid)])
							if search_ids:
								map_obj = map_prod_pool.browse(cr, uid, search_ids[0])
								mage_variant_ids.append(map_obj.mag_product_id)						
							else:
								if single_value_dic:
									context = single_value_dic
								mage_ids = self._export_specific_product(cr, uid, vid, template_sku,url, session, context)
								if mage_ids and mage_ids[0]>0:
									mage_variant_ids.append(mage_ids[1])					
						get_product_data['associated_product_ids'] = mage_variant_ids
						
					else:
						return [-1, str(id)+' Attribute Set Name not selected!!!']					
				else :
					for obj in obj_pro.product_variant_ids:
						vid = obj.id
						search_ids = map_prod_pool.search(cr, uid, [('oe_product_id','=',vid)])
						if search_ids:
							map_obj = map_prod_pool.browse(cr, uid, search_ids[0])
							mage_variant_ids.append(map_obj.mag_product_id)
						else:
							mage_ids = self._export_specific_product(cr, uid, vid, template_sku, url, session, context)
							if mage_ids[0]>0:
								name  = obj_pro.name
								price = obj_pro.list_price or 0.0
								map_tmpl_pool.create(cr, uid, {'template_name':id, 'erp_template_id':id, 'mage_product_id':mage_ids[1], 'base_price':price, 'is_variants':False, 'created_by':'Odoo'})
						return mage_ids
			else:
				return [-2, str(id)+' No Variant Ids Found!!!']		
			get_product_data['price_changes'] = mage_price_changes
			get_product_data['visibility'] = 4
			get_product_data['name'] = obj_pro.name
			get_product_data['short_description'] = obj_pro.description_sale or 'None'
			get_product_data['description'] = obj_pro.description or 'None'
			get_product_data['price'] = obj_pro.list_price or 0.00
			get_product_data['weight'] = obj_pro.weight_net or 0.00
			get_product_data['categories'] = prod_catg
			get_product_data['websites'] = [1]
			get_product_data['status'] = 1
			get_product_data['tax_class_id'] = '0'		
			if mage_set_id:
				newprod_data = ['configurable', mage_set_id, template_sku, get_product_data]
				self.pool.get('product.template').write(cr, uid, id, {'prod_type':'configurable'})	
				try:
					mage_product_id = server.call(session, 'product.create', newprod_data)
				except xmlrpclib.Fault, e:
					return [0, str(id)+str(e)]
				if mage_product_id:
					server.call(session, 'product_stock.update', [mage_product_id,{'manage_stock':1,'is_in_stock':1}])
				map_tmpl_pool.create(cr, uid, {'template_name':id, 'erp_template_id':id, 'mage_product_id':mage_product_id, 'base_price': get_product_data['price'], 'is_variants':True, 'created_by':'Odoo'})
				server.call(session, 'magerpsync.template_map', [{'name':obj_pro.name,'mage_template_id':mage_product_id,'erp_template_id':id,'created_by':'Odoo'}])
				if mage_product_id:
					if obj_pro.image:
						file = {'content':obj_pro.image,'mime':'image/jpeg'}
						type = ['image','small_image','thumbnail']
						pic = {'file':file,'label':'Label', 'position':'100','types':type, 'exclude':1}
						image = [mage_product_id,pic]
						k = server.call(session,'catalog_product_attribute_media.create',image)
				return [1,mage_product_id]
			else:
				return [-3, str(id)+' Attribute Set Name not found!!!']

	#############################################
	##  export bulk/selected products template ##
	#############################################
	
	def export_bulk_product_template(self, cr, uid, context=None):
		if context is None:
			context = {}
		text =  ''
		text1 = text2= ''
		fail_ids= []
		error_ids=[]
		up_error_ids =[]
		success_up_ids=[]
		success_exp_ids= []
		get_product_data = {}
		bulk_ids = context.get('active_ids')	
		map_obj = self.pool.get('magento.product.template')
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]
			for l in bulk_ids:
				search = map_obj.search(cr,uid,[('template_name','=',l)])
				if not search:
					pro = self._export_specific_template(cr, uid, l, url, session, context)					
					if pro:
						if pro[0] > 0:
							success_exp_ids.append(l)
						else:
							error_ids.append(pro[1])
				else :
					map_id = self.pool.get('magento.product.template').browse(cr,uid,search[0])
					if map_id.need_sync == 'Yes':
						pro_update = self._update_specific_product_template(cr, uid,  search[0], url, session, context)
						if pro_update:
							if pro_update[0] > 0:
								success_up_ids.append(pro_update[1])
							else:
								up_error_ids.append(pro_update[1])
					else:
						fail_ids.append(l)
			if success_exp_ids:
				text = "\nThe Listed Product Template ids %s has been created on magento."%(success_exp_ids)
			if fail_ids:
				text += "\nSelected product Template ids %s are already synchronized on magento."%(fail_ids)
			if error_ids:
				text += '\nThe Listed Product Template ids %s does not synchronized on magento.'%error_ids
			if text:
				self.pool.get('magento.sync.history').create(cr,uid,{'status':'yes','action_on':'product','action':'b','error_message':text})
			if success_up_ids:
				text1 = '\nThe Listed Product Template ids %s has been successfully updated to Magento. \n'%success_up_ids
				self.pool.get('magento.sync.history').create(cr,uid,{'status':'yes','action_on':'product','action':'c','error_message':text1})
			if up_error_ids:
				text2 = '\nThe Listed Product Template ids %s does not updated on magento.'%up_error_ids
				self.pool.get('magento.sync.history').create(cr,uid,{'status':'no','action_on':'product','action':'c','error_message':text2})
			partial = self.pool.get('message.wizard').create(cr, uid, {'text':text+text1+text2})
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

	#############################################`
	##    		update all products		       ##
	#############################################
	def update_products(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		text = text1 = ''
		up_error_ids = []
		success_ids =[]
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]
			server = xmlrpclib.Server(url)
			map_id = self.pool.get('magento.product.template').search(cr,uid,[('need_sync','=','Yes')])
			pro_ids = self.pool.get('product.template').search(cr, uid, [], context=context)
			if not map_id or not pro_ids:
				raise osv.except_osv(_('Information'), _("No product(s) Template has been found to be Update on Magento!!!"))
			if map_id:
				for i in map_id:
					pro_update=self._update_specific_product_template(cr, uid, i, url, session, context)
					if pro_update:
						if pro_update[0] != 0:
							success_ids.append(pro_update[1])
						else:
							up_error_ids.append(pro_update[1])
				if success_ids:
					text = 'The Listed Product ids %s has been sucessfully updated to Magento. \n'%success_ids
					self.pool.get('magento.sync.history').create(cr,uid,{'status':'yes','action_on':'product','action':'c','error_message':text})
				if up_error_ids:
					text1 = 'The Listed Product ids %s does not updated on magento.'%up_error_ids
					self.pool.get('magento.sync.history').create(cr,uid,{'status':'no','action_on':'product','action':'c','error_message':text1})
				text2 = text+text1
				if not text2:
					raise osv.except_osv(_('Information'), _("No product(s) has been found to be Update on Magento!!!"))
				partial = self.pool.get('message.wizard').create(cr, uid, {'text':text2})
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

	#############################################
	##    		update specific product	       ##
	#############################################
	def _update_specific_product(self, cr, uid, id, url, session, context):
		server = xmlrpclib.Server(url)
		get_product_data = {}
		pro_obj = self.pool.get('magento.product').browse(cr, uid, id)
		pro_id = pro_obj.oe_product_id
		mage_id = pro_obj.mag_product_id
		if pro_id and mage_id:
			prod_catg = []
			quantity = 0
			stock = 0
			price_extra=0
			obj_pro = self.pool.get('product.product').browse(cr, uid, pro_id, context)
			for j in obj_pro.categ_ids:
				mage_categ_id = self.sync_categories(cr, uid, url, session, j.id, context)
				prod_catg.append(mage_categ_id)
			if obj_pro.categ_id.id:
				mage_categ_id = self.sync_categories(cr, uid, url, session, obj_pro.categ_id.id, context)
				prod_catg.append(mage_categ_id)
			if obj_pro.attribute_value_ids:
				for value_id in obj_pro.attribute_value_ids:						
					get_product_data[value_id.attribute_id.name] = value_id.name
					pro_attr_id = value_id.attribute_id.id
					search_price_id = self.pool.get('product.attribute.price').search(cr, uid, [('product_tmpl_id','=',obj_pro.product_tmpl_id.id),('value_id','=',value_id.id)])
					if search_price_id:
						price_extra += self.pool.get('product.attribute.price').browse(cr,uid, search_price_id[0]).price_extra
			get_product_data['name'] = obj_pro.name
			get_product_data['price'] = obj_pro.list_price+price_extra or 0.00
			get_product_data['weight'] = obj_pro.weight_net or 0.00
			get_product_data['categories'] = prod_catg
			update_data = [mage_id, get_product_data]
			try:
				pro = server.call(session, 'product.update', update_data)
				self.pool.get('magento.product').write(cr, uid, id, {'need_sync':'No'})
			except xmlrpclib.Fault, e:
				return [0, str(pro_id)+str(e)]
			if pro and obj_pro.qty_available>0:
				quantity = obj_pro.qty_available
				stock = 1
			con_pool = self.pool.get('magento.configure')
			connection = con_pool.search(cr, uid, [('active','=',True),('inventory_sync','=','enable')])
			if connection:
				server.call(session, 'product_stock.update', [mage_id, {'manage_stock':1, 'qty':quantity,'is_in_stock':stock}])
			return  [1, pro_id]

	#############################################
	##    		single products	create 	       ##
	#############################################
	def prodcreate(self, cr, uid, url, session, pro_id, prodtype, prodsku, put_product_data, context):
		stock = 0
		quantity = 0
		server = xmlrpclib.Server(url)
		if put_product_data['currentsetname']:
			current_set = put_product_data['currentsetname']
		else:
			currset = server.call(session, 'product_attribute_set.list')
			current_set = currset[0].get('set_id')
		newprod = [prodtype, current_set, prodsku, put_product_data]
		try:
			pro = server.call(session, 'product.create', newprod)
		except xmlrpclib.Fault, e:
			return [0, str(pro_id)+str(e)]
		if pro:
			oe_product_qty = self.pool.get('product.product').browse(cr,uid,pro_id).qty_available
			if oe_product_qty > 0:
				quantity = oe_product_qty
				stock = 1
			con_pool = self.pool.get('magento.configure')
			connection = con_pool.search(cr, uid, [('active','=',True),('inventory_sync','=','enable')])
			if connection:
				server.call(session, 'product_stock.update', [pro,{'manage_stock':1,'qty':quantity,'is_in_stock':stock}])
			self.pool.get('magento.product').create(cr, uid, {'pro_name':pro_id, 'oe_product_id':pro_id, 'mag_product_id':pro, 'need_sync':'No', 'created_by':'Odoo'})
			cr.commit()
			server.call(session, 'magerpsync.product_map', [{'name':put_product_data['name'],'mage_product_id':pro,'erp_product_id':pro_id, 'created_by':'Odoo'}])
			return  [1, pro]
	
	#############################################
	##    		Specific product sync	       ##
	#############################################
	def _export_specific_product(self, cr, uid, id, template_sku, url, session,context):
		"""
		@param code: product Id.
		@param context: A standard dictionary
		@return: list
		"""
		get_product_data = {}
		if context is None:
			context = {}
		else:
			get_product_data.update(context)
		prod_catg = []
		map_variant=[]		
		pro_attr_id = 0
		price_extra = 0
		server = xmlrpclib.Server(url)
		mag_pro_pool = self.pool.get('magento.product')
		if id:
			obj_pro = self.pool.get('product.product').browse(cr, uid, id, context)
			for i in obj_pro.categ_ids:
				mage_categ_id = self.sync_categories(cr, uid, url, session, i.id, context)
				prod_catg.append(mage_categ_id)
			if obj_pro.categ_id.id:
				mage_categ_id = self.sync_categories(cr, uid, url, session, obj_pro.categ_id.id, context)
				prod_catg.append(mage_categ_id)
			sku = obj_pro.default_code or 'Ref %s'%id
			if template_sku == sku:
				sku = 'Varinat %s'%id			
			get_product_data['currentsetname'] = ""
			if obj_pro.attribute_value_ids:
				for value_id in obj_pro.attribute_value_ids:
					attrname = value_id.attribute_id.name.lower().replace(" ","_").replace("-","_")	
					valuename = value_id.name				
					get_product_data[attrname] = valuename					
					pro_attr_id = value_id.attribute_id.id
					search_price_id = self.pool.get('product.attribute.price').search(cr, uid, [('product_tmpl_id','=',obj_pro.product_tmpl_id.id),('value_id','=',value_id.id)])
					if search_price_id:
						price_extra += self.pool.get('product.attribute.price').browse(cr,uid, search_price_id[0]).price_extra
				mage_attr_pool  = self.pool.get('magento.product.attribute')
				attr_search_ids = mage_attr_pool.search(cr, uid, [('erp_id','=',pro_attr_id)])
				if attr_search_ids:
					get_product_data['currentsetname'] = obj_pro.product_tmpl_id.attribute_set_id.name
					get_product_data['visibility'] = 1
			get_product_data['name'] = obj_pro.name
			get_product_data['short_description'] = obj_pro.description_sale or ' '
			get_product_data['description'] = obj_pro.description or ' '
			get_product_data['price'] = obj_pro.list_price+price_extra or 0.00
			get_product_data['weight'] = obj_pro.weight_net or 0.00
			get_product_data['categories'] = prod_catg
			get_product_data['websites'] = [1]
			get_product_data['status'] = 1
			get_product_data['tax_class_id'] = '0'
			if obj_pro.type in ['product','consu']:
				prodtype = 'simple'
			else:
				prodtype = 'virtual'	
			self.pool.get('product.product').write(cr, uid, id, {'prod_type':prodtype})		
			pro = self.prodcreate(cr, uid, url, session, id, prodtype,sku, get_product_data, context)
			if pro and pro[0] != 0:
				if obj_pro.image:
					file = {'content':obj_pro.image,'mime':'image/jpeg'}
					type = ['image','small_image','thumbnail']
					pic = {'file':file,'label':'Label', 'position':'100','types':type, 'exclude':1}
					image = [pro[1],pic]
					k = server.call(session,'catalog_product_attribute_media.create',image)
			return pro


	#############################################
	##    		export all products		       ##
	#############################################
	
	def export_products(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		error_ids = []
		success_ids = []
		synced_ids = []
		catg_dict = {}
		catg_list = []
		text = text1 = ''
		map_tmpl_pool = self.pool.get('magento.product.template')
		pro_dt = len(self.pool.get('product.attribute').search(cr, uid, [], context=context))
		map_dt = len(self.pool.get('magento.product.attribute').search(cr, uid, []))
		pro_op = len(self.pool.get('product.attribute.value').search(cr, uid, [], context=context))
		map_op = len(self.pool.get('magento.product.attribute.value').search(cr, uid, []))
		if pro_dt != map_dt or pro_op != map_op:
			raise osv.except_osv(('Warning'),_('Please, first map all ERP Product attributes and it\'s all options'))
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]
			server = xmlrpclib.Server(url)
			map_id = map_tmpl_pool.search(cr,uid,[])
			for m in map_id:
				map_obj = map_tmpl_pool.browse(cr,uid,m)
				synced_ids.append(map_obj.erp_template_id)
			erp_pro = self.pool.get('product.template').search(cr,uid,[('id', 'not in', synced_ids)], context=context)
			if not erp_pro:
				raise osv.except_osv(_('Information'), _("No new product(s) Template found to be Sync."))
			if erp_pro:
				for l in erp_pro:
					pro = self._export_specific_template(cr, uid, l, url, session, context)
					if pro:
						if pro[0] > 0:
							success_ids.append(l)
						else:
							error_ids.append(pro[1])
			if success_ids:
				text = 'The Listed Product Template ids %s has been sucessfully Synchronized to Magento. \n'%success_ids
			if error_ids:
				text1 = 'Error in Listed Product Template ids %s .'%error_ids
			partial = self.pool.get('message.wizard').create(cr, uid, {'text':text+text1})
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

	def update_Customers(self,cr,uid,ids,context=None):	
		if context is None:
			context = {}	
		count = 0
		text = text1 = ''
		error_ids = []
		street=[]
		get_customer_data = {}
		get_address_data = {}
		connection = self.pool.get('magento.configure')._create_connection(cr,uid,context)
		if connection:
			url = connection[0]
			session = connection[1]
			server = xmlrpclib.Server(url)
			map_id = self.pool.get('magento.customers').search(cr,uid,[('need_sync','=','Yes')])
			cus_ids = self.pool.get('res.partner').search(cr,uid,[])
			if not map_id:
				raise osv.except_osv(_('Information'), _("No customer(s) has been found to be Update on Magento!!!"))
			if map_id:
				for i in map_id:
					cus_obj = self.pool.get('magento.customers').browse(cr,uid,i)
					cus_id = cus_obj.oe_customer_id
					mage_cus_id = cus_obj.mag_customer_id
					try:
						mage_add_id = int(cus_obj.mag_address_id)
					except:
						mage_add_id = 0
					if cus_id in cus_ids and mage_cus_id:						
						obj_cus = self.pool.get('res.partner').browse(cr,uid,cus_id)
						name=obj_cus.name.split(' ',1)
						if len(name)>1:
							get_customer_data['firstname']=name[0]
							get_customer_data['lastname']=name[1]
						else:
							get_customer_data['firstname']=name[0]
							get_customer_data['lastname']=name[0]						
						if obj_cus.country_id.id:
							code=self.pool.get('res.country').browse(cr,uid,obj_cus.country_id.id).code
							get_address_data['country_id']=code
						else:
							get_address_data['country_id']='IN'
						if obj_cus.state_id:
							mage_region_id=self.get_mage_region_id(cr, uid, url, session, obj_cus.state_id.name, code)
							if mage_region_id:
								get_address_data['region'] = mage_region_id
							else:
								get_address_data['region'] = obj_cus.state_id.name					
						else:
							get_address_data['region'] = 'None'
					 
						get_address_data['region']=obj_cus.state_id.name or 'None'			
						street.append(obj_cus.street or 'None')
						street.append(obj_cus.street2 or 'None')
						
						get_address_data['street']=street			
						get_address_data['city']=obj_cus.city or 'None'			 
						get_address_data['postcode']=obj_cus.zip or 'None'
						get_address_data['telephone']=obj_cus.phone or 'Not available'			 
						get_address_data['fax']=obj_cus.fax or 'Not available'			
						get_address_data['lastname']=get_customer_data['lastname']
						get_address_data['firstname']=get_customer_data['firstname']										
						try:
							if mage_cus_id>0:
								update_data = [mage_cus_id, get_customer_data]
								server.call(session, 'customer.update', update_data)							
							if mage_add_id>0:
								update_data = [mage_add_id, get_address_data]								
								server.call(session, 'customer_address.update', update_data)
							count = count + 1
							self.pool.get('magento.customers').write(cr, uid, i, {'need_sync':'No'})
						except xmlrpclib.Fault, e:
							error_ids.append(cus_id)				
				if count:
					text = '%s Customer has been sucessfully updated to Magento. \n'%count
					self.pool.get('magento.sync.history').create(cr,uid,{'status':'yes','action_on':'customer','action':'c','error_message':text})
				if error_ids:
					text1 = 'The Listed Customer ids %s does not updated on magento.'%error_ids
					self.pool.get('magento.sync.history').create(cr,uid,{'status':'no','action_on':'customer','action':'c','error_message':text1})
				partial = self.pool.get('message.wizard').create(cr, uid, {'text':text+text1})
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

	def get_mage_region_id(self, cr, uid, url, session, region, country_code, context=None):
		""" 
		@return magneto region id 
		"""
		region_obj = self.pool.get('magento.region')
		map_id = region_obj.search(cr,uid,[('country_code','=',country_code)])
		if not map_id:
			return_id = self.pool.get('region.wizard')._sync_mage_region(cr, uid, url, session, country_code)			
		region_ids = region_obj.search(cr,uid,[('name','=',region),('country_code','=',country_code)])
		if region_ids:
			id = region_obj.browse(cr,uid,region_ids[0]).mag_region_id
			return id
		else:		
			return 0



class magento_product_template(osv.osv):
	_name="magento.product.template"
	_order = "need_sync"
	_description = "Magento Product Template"
	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		vals['erp_template_id']=vals['template_name']
		if not vals.has_key('base_price'): 	
		# if float(vals['base_price'])<0.00000000000001:
			vals['base_price']=self.pool.get('product.template').browse(cr,uid,vals['erp_template_id']).list_price
		return super(magento_product_template, self).create(cr, uid, vals, context=context)
	_columns = {		
		'template_name':fields.many2one('product.template', 'Template Name'),
		'erp_template_id':fields.integer('Odoo`s Template Id'),
		'mage_product_id':fields.integer('Magento`s Product Id'),
		'base_price': fields.float('Base Price(excl. impact)'),
		'is_variants':fields.boolean('Is Variants'),
		'created_by':fields.char('Created By', size=64),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),		
		'need_sync': fields.selection([('Yes','Yes'),('No','No')],'Update Required'),
	}
	_defaults={
		'need_sync':'No',
	}

	def inactive_default_variant(self, cr, uid, product_template_id, context):
		varinat_ids = self.pool.get('product.template').browse(cr,uid,product_template_id).product_variant_ids
		for vid in varinat_ids:
			var_pool = self.pool.get('product.product')
			att_line_ids = var_pool.browse(cr, uid, vid.id).attribute_line_ids
			if not att_line_ids:
				var_pool.write(cr,uid,[vid.id],{'active':0})
		return True
	
	def create_product_template(self, cr, uid, data, context=None):
		"""Create and update a product by any webservice like xmlrpc.
		@param data: details of product fields in list.
		"""
		if context is None:
			context = {}
		temp_dic = {}		
		product_id = 0
		if data.has_key('name')  and data['name']:
			temp_dic['name'] = urllib.unquote_plus(data.get('name').encode('utf8'))
		if data.has_key('default_code') and data['default_code']:
			temp_dic['default_code'] = urllib.unquote_plus(data.get('default_code').encode('utf8'))
		if data.has_key('description') and data['description']:
			temp_dic['description'] = urllib.unquote_plus(data.get('description').encode('utf8'))
		if data.has_key('description_sale') and data['description_sale']:
			temp_dic['description_sale'] = urllib.unquote_plus(data.get('description_sale').encode('utf8'))
		temp_dic['list_price'] = data.get('list_price') or 0.00
		temp_dic['weight_net'] = data.get('weight_net') or 0.00
		# temp_dic['is_multi_variants'] = data.get('is_multi_variants')
		if data.has_key('standard_price'):
			temp_dic['standard_price'] = data.get('standard_price')
		else:
			temp_dic['weight'] = data.get('weight_net') or 0.00
		if data.has_key('weight'):
			temp_dic['weight'] = data.get('weight')
		else:
			temp_dic['weight'] = data.get('weight_net') or 0.00
		if data.has_key('type'):
			temp_dic['type'] = data.get('type')
		if data.has_key('categ_ids') and data.get('categ_ids'):
			categ_ids = data.get('categ_ids')
			temp_dic['categ_id'] = max(categ_ids)
			categ_ids.remove(max(categ_ids))
			temp_dic['categ_ids'] = [(6, 0, categ_ids)]
		if data.has_key('image'):
			temp_dic['image'] = data.get('image')
		if data.has_key('ean13'):
			temp_dic['ean13'] = data.get('ean13')
		if data.has_key('prod_type') and data.get('prod_type'):
			temp_dic['prod_type'] = data.get('prod_type')
		if data.has_key('set_id') and data.get('set_id'):
			# set_search = self.pool.get('magento.attribute.set').search(cr, uid, [('set_id','=',data.get('set_id'))])
			# if not set_search:		
			# 	return False		
			temp_dic['attribute_set_id'] = data.get('set_id')
		if data.get('method') == 'create':
			mage_product_id = data.get('mage_id')
			product_template_id = self.pool.get('product.template').create(cr, uid, temp_dic, context)
			self.create(cr, uid, {'template_name':product_template_id,'erp_template_id':product_template_id,'mage_product_id':mage_product_id,'base_price':temp_dic['list_price'],'is_variants':True,'created_by':'Magento'})
			self.inactive_default_variant(cr, uid, product_template_id, context)
			return product_template_id
		if data.get('method') == 'write':
			product_id = data.get('product_id')	
			self.pool.get('product.template').write(cr, uid, product_id, temp_dic, context)
			search_ids = self.search(cr, uid, [('erp_template_id','=', product_id)])
			if search_ids:				
				self.write(cr, uid, search_ids,{'need_sync':'No'})
			return True
		return False

	def create_attr_line(self,cr,uid,data): 
		att_dic = {}
		if data.has_key('product_tmpl_id')  and data['product_tmpl_id']:
			att_dic['product_tmpl_id'] = data.get('product_tmpl_id') 
		if data.has_key('attribute_id')  and data['attribute_id']:
			att_dic['attribute_id'] = data.get('attribute_id')
		if data.has_key('value_ids')  and data['value_ids']:
			value_ids = data.get('value_ids')
			att_dic['value_ids'] = [(6, 0, value_ids)]
		attr_line_id = self.pool.get('product.attribute.line').create(cr, uid, att_dic)
		return attr_line_id

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
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
	_defaults={
		'need_sync':'No',
	}

	def create_product(self, cr, uid, data, context=None):
		"""Create and update a product by any webservice like xmlrpc.
		@param data: details of product fields in list.
		"""
		if context is None:
			context = {}
		pro_dic = {}		
		product_id = 0	
		attr_val_ids = []	
		if data.has_key('default_code') and data['default_code']:
			pro_dic['default_code'] = urllib.unquote_plus(data.get('default_code').encode('utf8'))
		if data.has_key('ean13'):
				pro_dic['ean13'] = data.get('ean13')
		if data.has_key('set_id') and data.get('set_id'):	
			pro_dic['attribute_set_id'] = data.get('set_id')	
		if data.has_key('product_tmpl_id'):
			pro_dic['product_tmpl_id'] = data.get('product_tmpl_id')
			if data.has_key('attribute_value_ids'):
				attr_val_ids = data.get('attribute_value_ids')
				pro_dic['attribute_value_ids'] = [(6,0,attr_val_ids)]
		else:
			if data.has_key('name')  and data['name']:
				pro_dic['name'] = urllib.unquote_plus(data.get('name').encode('utf8'))			
			if data.has_key('description') and data['description']:
				pro_dic['description'] = urllib.unquote_plus(data.get('description').encode('utf8'))
			if data.has_key('description_sale') and data['description_sale']:
				pro_dic['description_sale'] = urllib.unquote_plus(data.get('description_sale').encode('utf8'))
			pro_dic['list_price'] = data.get('list_price') or 0.00
			pro_dic['weight_net'] = data.get('weight_net') or 0.00
			if data.has_key('standard_price'):
				pro_dic['standard_price'] = data.get('standard_price')
			else:
				pro_dic['weight'] = data.get('weight_net') or 0.00
			if data.has_key('weight'):
				pro_dic['weight'] = data.get('weight')
			else:
				pro_dic['weight'] = data.get('weight_net') or 0.00
			if data.has_key('type'):
				pro_dic['type'] = data.get('type')
			if data.has_key('categ_ids') and data.get('categ_ids'):
				categ_ids = data.get('categ_ids')
				pro_dic['categ_id'] = max(categ_ids)
				categ_ids.remove(max(categ_ids))
				pro_dic['categ_ids'] = [(6, 0, categ_ids)]
			if data.has_key('image'):
				pro_dic['image'] = data.get('image')		
			if data.has_key('prod_type') and data.get('prod_type'):
				pro_dic['prod_type'] = data.get('prod_type')					
		if data.get('method') == 'create':			
			product_pool = self.pool.get('product.product')
			mage_temp_pool = self.pool.get('magento.product.template')
			mage_product_id = data.get('mage_id')
			product_id = product_pool.create(cr, uid, pro_dic, context) 

			product_template_id = product_pool.browse(cr, uid, product_id).product_tmpl_id.id	
			if product_template_id:
				if attr_val_ids:
					for attr_val_id in attr_val_ids:						
						attr_id = self.pool.get('product.attribute.value').browse(cr, uid, attr_val_id).attribute_id.id
						search_ids = self.pool.get('product.attribute.line').search(cr, uid, [('product_tmpl_id','=',product_template_id),('attribute_id','=',attr_id)])
						if search_ids:
							self.pool.get('product.attribute.line').write(cr, uid, search_ids,{'value_ids':[(4,attr_val_id)]}) 
				search_ids = mage_temp_pool.search(cr, uid, [('erp_template_id','=', product_template_id)])
				if not search_ids:
					mage_temp_pool.create(cr, uid, {'template_name':product_template_id,'erp_template_id':product_template_id,'mage_product_id':mage_product_id,'base_price':pro_dic['list_price'],'created_by':'Magento'})
			
			self.create(cr, uid, {'pro_name':product_id,'oe_product_id':product_id,'mag_product_id':mage_product_id, 'created_by':'Magento'})
			if data.has_key('product_tmpl_id'):				
				search_ids = mage_temp_pool.search(cr, uid, [('erp_template_id','=', data.get('product_tmpl_id'))])
				if search_ids:
					mage_temp_pool.write(cr, uid,search_ids[0], {'need_sync':'No'})
			return product_id

		if data.get('method') == 'write':
			product_id = data.get('product_id')
			product_pool = self.pool.get('product.product')
			mage_temp_pool = self.pool.get('magento.product.template')
			product_pool.write(cr, uid, product_id, pro_dic, context)
			pro_tmpl_id = product_pool.browse(cr, uid, product_id).product_tmpl_id.id
			search_ids = self.search(cr, uid, [('oe_product_id','=', product_id)])
			if search_ids:				
				self.write(cr, uid, search_ids,{'need_sync':'No'})
			if pro_tmpl_id:				
				search_tmpl_ids = mage_temp_pool.search(cr, uid, [('erp_template_id','=', pro_tmpl_id)])
				if search_tmpl_ids:
					mage_temp_pool.write(cr, uid,search_tmpl_ids[0], {'need_sync':'No'})
			return True
		return False
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
		'need_sync':fields.selection([('Yes', 'Yes'),('No', 'No')],'Update Required'),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
	_defaults={
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
			categ_dic['name'] = urllib.unquote_plus(data.get('name').encode('utf8'))
		if data.has_key('type'):
			categ_dic['type'] = data.get('type')
		if data.has_key('parent_id'):
			categ_dic['parent_id'] = data.get('parent_id')
		if data.get('method') == 'create':
			mage_category_id = data.get('mage_id')
			category_id = self.pool.get('product.category').create(cr, uid, categ_dic, context)
			self.create(cr, uid,{'cat_name':category_id,'oe_category_id':category_id,'mag_category_id':mage_category_id,'created_by':'Magento'})
			return category_id
		if data.get('method') == 'write':
			category_id = data.get('category_id')
			self.pool.get('product.category').write(cr, uid, category_id, categ_dic, context)
			return True
		return False
magento_category()

class magento_customers(osv.osv):			
	_name="magento.customers"
	_order = 'id desc'
	_rec_name = "cus_name"
	_description = "Magento Customers"
	_columns = {		
		'cus_name':fields.many2one('res.partner', 'Customer Name'),		
		'oe_customer_id':fields.integer('Odoo Customer Id'),
		'mag_customer_id':fields.char('Magento Customer Id',size=50),
		'mag_address_id':fields.char('Magento Address Id',size=50),
		'need_sync':fields.selection([('Yes', 'Yes'),('No', 'No')],'Update Required'),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
	_defaults={					
		'need_sync':'No',
	}
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
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
magento_region()

			################## .............sale order Mapping.............##################

class magento_orders(osv.osv):
	_name="magento.orders"
	_order = 'id desc'
	_rec_name = "order_ref"
	_description = "Magento Orders"
	_columns = {
		'order_ref':fields.many2one('sale.order', 'Order Reference'),
		'oe_order_id':fields.integer('Odoo order Id'),
		'mag_orderIncrement_Id':fields.char('Magento order Id', size=100),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
	}
	
	def create_pricelist(self, cr, uid, data, context=None):
		"""create and search pricelist by any webservice like xmlrpc.
		@param code: currency code.
		@param context: A standard dictionary
		@return: pricelist_id
		"""
		if context is None:
			context = {}
		currency_ids = self.pool.get('res.currency').search(cr,uid,[('name','=',data['code'])])  or [False]
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
			product_pricelist_item_id = self.pool.get('product.pricelist.item').create(cr,uid,item_dict,context)
			return pricelist_id
		else:
			return pricelist_ids[0]	
	
	def _get_journal_code(self, cr, uid, string, sep=' ', context=None):
		tl = []
		for t in string.split(sep):
			t2 = t.title()[0]
			if t2.isalnum():
				tl.append(t2)
		code=''.join(tl)
		code=code[0:3]
		is_exist=self.pool.get('account.journal').search(cr, uid, [('code', '=',code)], context=context)
		if is_exist:
			for i in range(1,99):
				is_exist=self.pool.get('account.journal').search(cr, uid, [('code', '=',code+str(i))], context=context)
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
		res = self.pool.get('account.journal').search(cr, uid, [('type', '=','bank')], limit=1, context=context)[0]
		credit_account_id = self.pool.get('account.journal').browse(cr, uid, res, context).default_credit_account_id.id
		debit_account_id = self.pool.get('account.journal').browse(cr, uid, res, context).default_debit_account_id.id
		data['default_credit_account_id'] = credit_account_id
		data['default_debit_account_id'] = debit_account_id
		data['code'] = self._get_journal_code(cr, uid, data.get('name'),' ', context)
		payment_id = self.pool.get('account.journal').create(cr, uid, data, context)
		return payment_id

	def _get_product_id(self, cr, uid, product_data, context):
		pro_dic = {}
		category_id = 0
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]
			server = xmlrpclib.Server(url)			
			default_code = urllib.unquote_plus(product_data['sku'].encode('utf8'))
			prod_pool = self.pool.get('product.product')
			product_ids = prod_pool.search(cr,uid,[('default_code','=',default_code),('active','=',False)], context=context)
			if not product_ids:
				pro_dic['name'] = urllib.unquote_plus(product_data['name'].encode('utf8'))
				if product_data['product_type'] != 'simple':
					pro_dic['type'] = 'service'
				else:
					pro_dic['type'] = 'product'
				pro_dic['list_price'] = 0.00
				pro_dic['active'] = False
				pro_dic['default_code'] = default_code
				attribute_set_search = self.pool.get('magento.attribute.set').search(cr, uid, [])
				if attribute_set_search:
					pro_dic['attribute_set_id'] = attribute_set_search[0]
				categ_ids = self.pool.get('product.category').search(cr, uid, [('name','=','Shipping/Voucher')], context=context)
				if not categ_ids:
					category_id = self.pool.get('product.category').create(cr, uid, {'name':'Shipping/Voucher','type':'normal'}, context)
					pro_dic['categ_id'] = category_id
					self.pool.get('magento.category').create(cr, uid, {'cat_name':category_id,'oe_category_id':category_id,'mag_category_id':'-1', 'created_by':'Odoo'})
					# Magento mapping Entry				
					# server.call(session, 'magerpsync.category_map', [{'name':'Shipping/Voucher', 'mage_category_id':'0', 'erp_category_id':category_id, 'created_by':'Odoo'}])
				else:
					pro_dic['categ_id'] = categ_ids[0]

				product_id = prod_pool.create(cr, uid, pro_dic, context)
				tmpl_id = prod_pool.browse(cr, uid, product_id).product_tmpl_id.id
				if tmpl_id:
					self.pool.get('product.template').write(cr, uid, tmpl_id, {'active':False})
				self.pool.get('magento.product').create(cr, uid, {'pro_name':product_id, 'oe_product_id':product_id, 'mag_product_id':'-1', 'need_sync':'No', 'created_by':'Odoo'})
				server.call(session, 'magerpsync.product_map', [{'name':pro_dic['name'],'mage_product_id':0,'erp_product_id':product_id, 'created_by':'Odoo'}])
				return product_id
			else:
				return product_ids[0]
			
	def extra_order_line(self, cr, uid, data, context=None):	
		if context is None:
			context = {}
		line_dic = {}
		carrier_id = 0
		product_id = 0
		shipping_description = 'Default_Shipping'
		delivery_carrier = self.pool.get('delivery.carrier')
		sale_order_line = self.pool.get('sale.order.line')
		if data.has_key('coupon_code'):
			line_dic['name'] = data['coupon_code']
		if data.has_key('shipping_description') and data['shipping_description']:
			shipping_description = urllib.unquote_plus(data['shipping_description'].encode('utf8'))
			line_dic['name'] = shipping_description
		if data.has_key('discount'):
			line_dic['discount'] = data.get('discount')
		if data['product_type'] == 'shipping':
			mage_car_pool = self.pool.get('magento.delivery.carrier')
			carrier_ids = delivery_carrier.search(cr, uid, [('name','=',shipping_description)])
			product_id = self._get_product_id(cr, uid, data, context)
			if carrier_ids:
				carrier_id  = carrier_ids[0]
				search_carrier = mage_car_pool.search(cr, uid, [('name','=',carrier_id)])
				if search_carrier:
					product_id = mage_car_pool.browse(cr, uid, search_carrier[0]).product_id.id
				else:
					mage_car_pool.create(cr, uid, {'name':carrier_id, 'product_id':product_id, 'magento_id':'-1'})
			else:				
				dc_dict = {'name':shipping_description, 'product_id':product_id, 'partner_id':data['customer_id'],'normal_price':100.00}
				carrier_id  = delivery_carrier.create(cr, uid, dc_dict)
				mage_car_pool.create(cr, uid, {'name':carrier_id, 'product_id':product_id, 'magento_id':'-1'})
		if product_id:
			line_dic['order_id'] = data['order_id']
			line_dic['price_unit'] = data['price_unit']
			line_dic['product_id'] = product_id
			line_dic['product_uom_qty'] =  1
			line_dic['product_uom'] = self.pool.get('product.product').browse(cr, uid, product_id).uom_id.id or 1
			if data.has_key('tax_id'):
				taxes = data.get('tax_id')
				if type(taxes) != list:
					taxes = [data.get('tax_id')]
				line_dic['tax_id'] = [(6,0,taxes)]
			line_id = sale_order_line.create(cr, uid, line_dic)
			if carrier_id:
				self.pool.get('sale.order').write(cr, uid, data['order_id'], {'carrier_id':carrier_id})
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
			line_dic['name'] = urllib.unquote_plus(data.get('name').encode('utf8'))
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
		line_id = sale_order_line.create(cr, uid, line_dic)
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
		
		active_id=self.pool.get('magento.configure').search(cr, uid,[('state','=','enable')])
		if active_id:
			self.pool.get('magento.configure').write(cr, uid,active_id[0],{'state':'disable'})			
		if pick_id:
			pick_cancel=self.pool.get('stock.picking').action_cancel(cr,uid,pick_id)		
		order_cancel=self.pool.get('sale.order').action_cancel(cr,uid,[order_id])
		if active_id:
			self.pool.get('magento.configure').write(cr, uid,active_id[0],{'state':'enable'})	
		return True	
	
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
			cus_dic['country_id'] = country_ids[0]			
			if data.has_key('region') and data['region']:
				region = urllib.unquote_plus(data.get('region').encode('utf8'))
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
		if data.has_key('partner_id'):
			customer_id = data.get('partner_id')
		if data.has_key('name') and data['name']:
			cus_dic['name'] = urllib.unquote_plus(data.get('name').encode('utf8'))
		if data.has_key('email') and  data['email']:
			cus_dic['email'] = urllib.unquote_plus(data.get('email').encode('utf8'))
		if data.has_key('street') and data['street']:
			cus_dic['street'] = urllib.unquote_plus(data.get('street').encode('utf8'))
		if data.has_key('street2') and data['street2']:
			cus_dic['street2'] = urllib.unquote_plus(data.get('street2').encode('utf8'))
		if data.has_key('city') and data['city']:
			cus_dic['city'] = urllib.unquote_plus(data.get('city').encode('utf8'))
		cus_dic['type'] = data.get('type',False)
		cus_dic['zip'] = data.get('zip',False)
		cus_dic['phone'] = data.get('phone',False)
		cus_dic['fax'] = data.get('fax',False)
		if data.has_key('tag') and data["tag"]:
			tag = urllib.unquote_plus(data.get('tag').encode('utf8'))
			tag_ids = self.pool.get('res.partner.category').search(cr,uid,[('name','=',tag)], limit=1)
			if not tag_ids:
				tag_id = self.pool.get('res.partner.category').create(cr,uid,{'name':tag})
			else:
				tag_id = tag_ids[0]
			cus_dic['category_id'] = [(6,0,[tag_id])]
		if data.get('method') == 'create':
			customer_id = self.pool.get('res.partner').create(cr, uid,cus_dic)
			return customer_id
		if data.get('method') == 'write':
			self.pool.get('res.partner').write(cr, uid, customer_id, cus_dic)
			return customer_id
		return False
		
	def create_order_invoice(self,cr,uid,data):
		active_id=self.pool.get('magento.configure').search(cr, uid,[('state','=','enable')])
		if active_id:
			self.pool.get('magento.configure').write(cr, uid,active_id[0],{'state':'disable'})			
		inv_ids = self.pool.get('sale.order').manual_invoice(cr,uid,[data.get('order_id')])
		invoice_id = inv_ids['res_id']
		if data.has_key('date'):
			self.pool.get('account.invoice').write(cr, uid,invoice_id,{'date_invoice':data.get('date'), 'date_due':data.get('date') ,'internal_number':data['mage_inv_number']})
		self.pool.get('account.invoice').signal_workflow(cr, uid, [invoice_id],'invoice_open')
		if active_id:
			self.pool.get('magento.configure').write(cr, uid,active_id[0],{'state':'enable'})
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
		
	def sales_order_payment(self,cr,uid,payment,context=None):	
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
                            'type': 'receipt',
                         }
		if data.get('payment_rate_currency_id'):
			statement_vals['payment_rate_currency_id'] = data['payment_rate_currency_id']
			company_currency_id=self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
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
		active_id = self.pool.get('magento.configure').search(cr,uid,[('state','=','enable')])
		if active_id:
			self.pool.get('magento.configure').write(cr, uid, active_id[0], {'state': 'disable'})
		order_name = self.pool.get('sale.order').name_get(cr, uid, data['order_id'])
		pick_id = self.pool.get('stock.picking').search(cr, uid,[('origin','=',order_name[0][1])])
		if pick_id:
			self.pool.get('stock.picking').do_transfer(cr, uid, pick_id, context)			
			workflow.trg_validate(uid, 'sale.order',data['order_id'], 'ship_end', cr)			
			res =  True
		if active_id:
			self.pool.get('magento.configure').write(cr, uid, active_id[0], {'state': 'enable'})
		return res

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
			
		rec_id = data.get('product_id')
		context['stock_from'] = 'magento'
		assert rec_id, _('Active ID is not set in Context')

		mage_qty = data.get('new_quantity')		
		prod_obj_pool = self.pool.get('product.product')
		res_original = prod_obj_pool.browse(cr, uid, rec_id, context=context)
		location_id = 0
		if data.has_key('warehouse_id'):
			location_id = self.pool.get('stock.warehouse').browse(cr, uid, data.get('warehouse_id')).lot_stock_id.id	
		else:
			location_ids = self.pool.get('stock.warehouse').search(cr, uid, [], context=context)
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
			inventory_id = inventory_obj.create(cr , uid, {'name': _('INV: %s') % openerp.tools.ustr(res_original.name)}, context=context)
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

	def release_mage_order_from_hold(self, cr, uid, increment_id, url, session):
		server = xmlrpclib.Server(url)
		try:
			order_info = server.call(session,'order.info',[increment_id])
			if order_info['state'] == 'holded':
				server.call(session,'order.unhold',[increment_id])
			return  True
		except Exception,e:
			return False
	
magento_orders()

class account_invoice(osv.osv):
	_inherit = 'account.invoice'

	def mage_invoice_trigger(self, cr, uid, ids, context=None):
		sale_obj = self.pool.get('sale.order')
		for inv_id in ids:
			invoices = self.read(cr, uid, inv_id, ['origin','state'])
			if invoices['origin']:
				sale_ids = sale_obj.search(cr, uid, [('name','=',invoices['origin'])])
		##### manual_magento_invoice method is used to create an invoice on magento end #########
				if sale_ids:
					config_id = self.pool.get('magento.configure').search(cr,uid,[('state','=','enable'),('auto_invoice','=',True)])
					if len(config_id)>0:
						mage_invoice = self.manual_magento_invoice(cr, uid, sale_ids, context)
						if mage_invoice:
							return True
		return True

	def manual_magento_invoice(self, cr, uid, ids, context=None):		
		text = ''
		status = 'no'
		session = 0
		mage_invoice = False
		config_id = self.pool.get('magento.configure').search(cr,uid,[('state','=','enable')])
		if len(config_id)>1:
			text = 'Sorry, only one Active Configuration setting is allowed.'
		if not config_id:
			text = 'Please create the configuration part for connection!!!'
		else:
			obj = self.pool.get('magento.configure').browse(cr,uid,config_id[0])
			url = obj.name+'/index.php/api/xmlrpc'
			user = obj.user
			pwd = obj.pwd
			try:
				server = xmlrpclib.Server(url)
				session = server.login(user,pwd)
			except xmlrpclib.Fault, e:
				text = 'Invoice on magento cannot be done, Error %s Magento details are Invalid.'%e
			except IOError, e:
				text = 'Invoice on magento cannot be done, due to error, %s.'%e
			except Exception,e:
				text = 'Invoice on magento cannot be done, due to error in Magento Connection.'
			if session:
				map_id = self.pool.get('magento.orders').search(cr,uid,[('oe_order_id','in',ids)])
				if map_id:
					map_obj = self.pool.get('magento.orders').browse(cr,uid,map_id[0])
					increment_id = map_obj.mag_orderIncrement_Id
					self.pool.get('magento.orders').release_mage_order_from_hold(cr, uid, increment_id,  url, session)
					try:
						invoice_array = [increment_id, 0, 'Invoiced From Odoo', False]
						mage_invoice = server.call(session,'sales_order_invoice.create', invoice_array)
						text = 'Invoice of order %s has been sucessfully updated on magento.'%map_obj.order_ref.name
						status = 'yes'
					except Exception,e:
						if e.faultCode == 103:
							text = 'Order %s invoice cannot be done on magento, Because Magento order %s does not exist on magento.'%(map_obj.order_ref.name, increment_id)
						else:
							text = 'Invoice of order %s has been already updated on magento.'%map_obj.order_ref.name
							status = 'yes'
				else:
					text = 'Order invoice cannot be done from magento, Cause order id %s is created from Odoo.'%ids
		cr.commit()
		workflow.trg_validate(uid, 'sale.order',ids[0], 'invoice_end', cr)
		self.pool.get('magento.sync.history').create(cr,uid,{'status':status,'action_on':'order','action':'b','error_message':text})
		return mage_invoice

account_invoice()
			################## .............sale order inherit.............##################
			
class sale_order(osv.osv):
	_name="sale.order"
	_inherit="sale.order"

	# to do  still waiting for magento invoice cancel.......
	def manual_magento_order_cancel(self,cr,uid,ids,context=None):
		text = ''
		status = 'no'
		session = 0
		config_id=self.pool.get('magento.configure').search(cr,uid,[('active','=',True)])
		if len(config_id)>1:
			text = 'Sorry, only one Active Configuration setting is allowed.'
		if not config_id:
			text = 'Please create the configuration part for connection!!!'
		else:
			obj = self.pool.get('magento.configure').browse(cr,uid,config_id[0])
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
			if session:
				map_id=self.pool.get('magento.orders').search(cr,uid,[('oe_order_id','=',ids[0])])
				if map_id:
					map_obj=self.pool.get('magento.orders').browse(cr,uid,map_id[0])
					increment_id = map_obj.mag_orderIncrement_Id
					self.pool.get('magento.orders').release_mage_order_from_hold(cr, uid, increment_id,  url, session)
					try:
						server.call(session,'sales_order.cancel',[increment_id])
						text = 'sales order %s has been sucessfully canceled from magento.'%map_obj.order_ref.name
						status = 'yes'
					except Exception,e:
						text = 'Order %s cannot be canceled from magento, Because Magento order %s is in different state.'%(map_obj.order_ref.name,map_obj.mag_orderIncrement_Id)
				else:
					text = 'Order cannot be canceled from magento, cause %s order is created from Odoo.'%ids[0]		
			cr.commit()
			self.pool.get('magento.sync.history').create(cr,uid,{'status':status,'action_on':'order','action':'b','error_message':text})	
		return True

	def action_cancel(self, cr, uid, ids, context=None):
		super(sale_order, self).action_cancel(cr, uid, ids, context)
		cr.commit()
		######## manual_magento_order_cancel method is used to cancel an order on magento end ######
		config_id = self.pool.get('magento.configure').search(cr,uid,[('state','=','enable')])
		if len(config_id)>0:
			self.manual_magento_order_cancel(cr, uid, ids, context)
		return True

	def magento_ship_trigger(self, cr, uid, ids, context=None):
		for sale_id in ids:
			config_id = self.pool.get('magento.configure').search(cr,uid,[('state','=','enable'),('auto_ship','=',True)])
			if len(config_id)==1:
				order_name = self.browse(cr, uid, sale_id).name
				if order_name:
					cr.commit()
					self.manual_magento_shipment(cr, uid, ids, order_name, context)
		return True

	def manual_magento_shipment(self, cr, uid, ids, order_name, context=None):
		text = ''
		status = 'no'
		session = False
		mage_shipment = False
		config_id = self.pool.get('magento.configure').search(cr,uid,[('state','=','enable')])
		if len(config_id)>1:
			text = 'Sorry, only one Active Configuration setting is allowed.'
		if not config_id:
			text = 'Please create the configuration part for connection!!!'
		else:					
			obj = self.pool.get('magento.configure').browse(cr, uid, config_id[0])
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
			if session:
				if ids:
					map_id = self.pool.get('magento.orders').search(cr, uid, [('oe_order_id','in',ids)])
					if map_id:
						map_obj = self.pool.get('magento.orders').browse(cr, uid, map_id[0])
						increment_id = map_obj.mag_orderIncrement_Id
						h = self.pool.get('magento.orders').release_mage_order_from_hold(cr, uid, increment_id,  url, session)
						try:
							ship_array = [increment_id, [], 'Shipped From Odoo', False]
							mage_shipment = server.call(session,'order_shipment.create', ship_array)
							text = 'shipment of order %s has been successfully updated on magento.'%order_name
							status = 'yes'
						except xmlrpclib.Fault, e:
							if e.faultCode == 103:
								text = 'shipment of order %s cannot be done on magento. Because order %s does not exist on Magento.'%(order_name,increment_id)
							else:
								text = 'shipment of order %s has been already updated on magento.'%order_name
								status = 'yes'
					else:
						text = 'Order cannot be shipped from magento, Cause %s order is created from Odoo.'%order_name
		cr.commit()
		self.pool.get('magento.sync.history').create(cr,uid,{'status':status,'action_on':'order','action':'b','error_message':text})
		return mage_shipment
	
sale_order()

	########### .............stock partial picking inherit (wizard).............###########
	

class magento_customers(osv.osv):			
	_name="magento.customers"
	_order = 'id desc'
	_rec_name = "cus_name"
	_description = "Magento Customers"
	_columns = {		
		'cus_name':fields.many2one('res.partner', 'Customer Name'),		
		'oe_customer_id':fields.integer('Odoo Customer Id'),
		'mag_customer_id':fields.char('Magento Customer Id',size=50),
		'mag_address_id':fields.char('Magento Address Id',size=50),
		'need_sync':fields.selection([('Yes', 'Yes'),('No', 'No')],'Update Required'),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
	_defaults={					
		'need_sync':'No',
	}
magento_customers()

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

class magento_attribute_set(osv.osv):
	_name = "magento.attribute.set"
	_description = "Magento Attribute Set"
	_order = 'set_id'

	_columns = {
		'name':fields.char('Magento Attribute Set'),
		'attribute_ids':fields.many2many('product.attribute', 'product_attr_set','set_id','attribute_id','Product Attributes', readonly=True, help="Magento Set attributes will be handle only at magento."),
		'set_id':fields.integer('Magento Set Id', readonly=True),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}

magento_attribute_set()


class magento_product_attribute(osv.osv):
	_name = "magento.product.attribute"
	_order = 'create_date'
	_description = "Magento Product Attribute"


	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		vals['erp_id'] = vals['name']	
		# vals['created_by'] = 'Magento'
		return super(magento_product_attribute, self).create(cr, uid, vals, context=context)
	
	def write(self,cr,uid,ids,vals,context=None):
		if context is None:
			context = {}
		if vals.has_key('name'):
			vals['erp_id']=vals['name']	
		return super(magento_product_attribute,self).write(cr,uid,ids,vals,context=context)
	
	_columns = {
		'name':fields.many2one('product.attribute', 'Product Attribute'),
		'erp_id':fields.integer('Odoo`s Attribute Id'),	
		'mage_id':fields.integer('Magento`s Attribute Id'),
		'mage_attribute_set_name':fields.char('Magento`s Attribute Set Name', readonly=True, size=255),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
magento_product_attribute()

class magento_product_attribute_value(osv.osv):			
	_name="magento.product.attribute.value"
	_order = 'create_date'
	_description = "Magento Product Attribute Value"
	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		vals['erp_id']=vals['name']	
		return super(magento_product_attribute_value, self).create(cr, uid, vals, context=context)
	
	def write(self,cr,uid,ids,vals,context=None):
		if context is None:
			context = {}
		if vals.has_key('name'):
			vals['erp_id']=vals['name']	
		return super(magento_product_attribute_value,self).write(cr,uid,ids,vals,context=context)
		
	_columns = {
		'name':fields.many2one('product.attribute.value', 'Attribute Value'),
		'erp_id':fields.integer('Odoo`s Attribute Value Id'),	
		'mage_id':fields.integer('Magetno`s Attribute Value Id'),
		'create_date':fields.datetime('Created Date'),
		'write_date':fields.datetime('Updated Date'),
		'created_by':fields.char('Created By', size=64)
	}
magento_product_attribute_value()


class magento_delivery_carrier(osv.osv):
	_name = 'magento.delivery.carrier'
	_description = 'Magento Delivery Carrier'

	_columns = {
		'name':fields.many2one('delivery.carrier','Odoo Delivery Carrier'),
		'product_id':fields.many2one('product.product','Odoo Delivery Product'),
		'magento_id':fields.char('Magento Carrier Id'),
	}
magento_delivery_carrier()

	###############  inherited Models ###################


class product_attribute_line(osv.osv):
	_inherit = "product.attribute.line"

	def onchange_attribute_set_id(self, cr, uid, ids, set_id, context=None):
		result = {}
		if set_id:
			obj = self.pool.get("magento.attribute.set").browse(cr, uid, set_id)
			attribute_ids = [x.id for x in obj.attribute_ids]
			result['domain'] = {'attribute_id': [('id','in',attribute_ids)]}
		return result

class product_template(osv.osv):
	_inherit = "product.template"
	_columns = {
    	'prod_type': fields.selection([('simple','Simple Product'),('grouped','Grouped Product'),('configurable','Configurable Product'),('virtual','Virtual Product'),('bundle','Bundle Product'),('downloadable','Downloadable Product')],'Magento Product Type',size=100, readonly=True),
        'categ_ids': fields.many2many('product.category','product_categ_rel','product_id','categ_id','Product Categories'),
        'attribute_set_id': fields.many2one('magento.attribute.set','Magento Attribute Set', help ="Selected magento attribute sets will show all possible attributes belong to selected sets",required=False),
	}
	def write(self, cr, uid, ids, vals, context=None):	
		map_obj = self.pool.get('magento.product.template')
		if type(ids) == list:
			for id in ids:
				map_ids = map_obj.search(cr, uid, [('template_name', '=', id)])
				if map_ids:
					map_obj.write(cr, uid, map_ids[0], {'need_sync':'Yes'})
				for obj in self.browse(cr, uid, id).product_variant_ids:
					pro_map_ids = self.pool.get('magento.product').search(cr, uid, [('pro_name', '=', obj.id)])
					if pro_map_ids:
						self.pool.get('magento.product').write(cr, uid, pro_map_ids[0], {'need_sync':'Yes'})			
		return super(product_template, self).write(cr, uid, ids, vals, context=context)
product_template()

class product_product(osv.osv):	
	_inherit= 'product.product'

	def write(self, cr, uid, ids, vals, context=None):	
		map_obj = self.pool.get('magento.product')
		tmpl_obj = self.pool.get('magento.product.template')
		if type(ids) == list:
			for id in ids:
				map_ids = map_obj.search(cr, uid, [('pro_name', '=', id)])
				if map_ids:
					map_obj.write(cr, uid, map_ids[0], {'need_sync':'Yes'})	
				tmpl_id = self.browse(cr, uid, id).product_tmpl_id.id	
				tmpl_map_ids = tmpl_obj.search(cr, uid, [('template_name', '=', tmpl_id)])
				if tmpl_map_ids:
					tmpl_obj.write(cr, uid, tmpl_map_ids[0], {'need_sync':'Yes'})
		return super(product_product,self).write(cr, uid, ids, vals, context=context)

product_product()

class product_category(osv.osv):	
	_inherit = 'product.category'

	def write(self, cr, uid, ids, vals, context=None):
		map_obj = self.pool.get('magento.category')		
		if type(ids) == list:
			for id in ids:
				map_ids = map_obj.search(cr, uid, [('oe_category_id', '=', id)])
				if map_ids:
					map_obj.write(cr, uid, map_ids[0], {'need_sync':'Yes'})
		return super(product_category,self).write(cr,uid,ids,vals,context=context)

product_category()

class res_partner(osv.osv):
	_inherit= 'res.partner'

	def write(self, cr, uid, ids, vals, context=None):	
		map_obj = self.pool.get('magento.customers')
		if type(ids) == list:
			for id in ids:
				map_ids = map_obj.search(cr, uid, [('oe_customer_id', '=', id)])
				if map_ids:
					map_obj.write(cr, uid, map_ids[0], {'need_sync':'Yes'})
		return super(res_partner,self).write(cr,uid,ids,vals,context=context)
		
res_partner()
# END