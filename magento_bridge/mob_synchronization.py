 # -*- coding: utf-8 -*-
##############################################################################
#		
#    Odoo, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################

import xmlrpclib
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import logging
_logger = logging.getLogger(__name__)

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

	def sync_attribute_set(self, cr, uid, data, context):
		erp_set_id = 0
		set_dic = {}
		res = False
		set_pool = self.pool.get('magento.attribute.set')

		if data.has_key('name') and data.get('name'):
			search_ids = set_pool.search(cr, uid, [('name','=',data.get('name'))])
			if not search_ids:
				set_dic['name'] = data.get('name')
				if data.has_key('set_id') and data.get('set_id'):
					set_dic['set_id'] = data.get('set_id')
				set_dic['created_by'] = 'Magento'
				set_dic['instance_id'] = context.get('instance_id')
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
					dic['instance_id'] = context.get('instance_id')
					res = set_pool.write(cr, uid, erp_set_id, dic, context)
		return res

	#############################################
	## 	 Export Attributes and values          ##
	#############################################
	def export_attributes_and_their_values(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		map_dic = []
		map_dict = {}
		error_message = ''
		attribute_count = 0
		attribute_pool = self.pool.get('product.attribute')
		attribute_value_pool = self.pool.get('product.attribute.value')
		attribute_mapping_pool = self.pool.get('magento.product.attribute')
		value_mapping_pool = self.pool.get('magento.product.attribute.value')		
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)		
		if connection:
			url = connection[0]
			session = connection[1]
			context['instance_id'] = connection[2]
			map_id = attribute_mapping_pool.search(cr,uid,[('instance_id','=',context.get('instance_id'))])			
			for m in map_id:
				map_obj = attribute_mapping_pool.browse(cr,uid,m)
				map_dic.append(map_obj.erp_id)
				map_dict.update({map_obj.erp_id:map_obj.mage_id})
			attribute_ids = attribute_pool.search(cr, uid, [], context=context)
			if attribute_ids:
				for attribute_id in attribute_ids:
					attribute_obj = attribute_pool.browse(cr, uid, attribute_id, context)
					if attribute_id not in map_dic:
						name = attribute_obj.name
						label = attribute_obj.name
						attribute_response = self.create_product_attribute(cr, uid, url, session, attribute_id, name, label, context)
					else:
						mage_id = map_dict.get(attribute_id)
						attribute_response = [int(mage_id)]
					if attribute_response[0] == 0:
						error_message = error_message + attribute_response[1]
					else:
						mage_id = attribute_response[0]
						for value_id in attribute_obj.value_ids:
							if not value_mapping_pool.search(cr,uid,[('erp_id','=',value_id.id),('instance_id','=',context.get('instance_id'))]):
								value_obj = attribute_value_pool.browse(cr, uid, value_id.id, context)
								name = value_obj.name
								position = value_obj.sequence
								value_response = self.create_attribute_value(cr, uid, url, session, mage_id, value_id.id, name, position, context)
								if value_response[0] == 0:
									error_message = error_message + value_response[1]
						attribute_count += 1
			else:
				error_message = "No new Attribute(s) Found To Be Export At Magento!!!"
			if attribute_count:
				error_message += "\n %s Attribute(s) and their value(s) successfully Synchronized To Magento."%(attribute_count)
			partial = self.pool.get('message.wizard').create(cr, uid, {'text':error_message})
			return { 
				'name':_("Message"),
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

	def create_product_attribute(self, cr, uid, url, session, attribute_id, name, label, context=None):
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
				mage_id = server.call(session, 'product_attribute.create', [attrribute_data])				
			except xmlrpclib.Fault, e:
				return [0,'\nError in creating Attribute (Code: %s).%s'%(name,str(e))]
			if mage_id:
				self.pool.get('magento.product.attribute').create(cr, uid, {
																		'name':attribute_id, 
																		'erp_id':attribute_id, 
																		'mage_id':mage_id,
																		'instance_id':context.get('instance_id'),
																		})

				server.call(session, 'magerpsync.attribute_map', [{	'name':name, 
																	'mage_attribute_id':mage_id, 
																	'erp_attribute_id':attribute_id
																}])	
				return [mage_id,'']	

	def create_attribute_value(self, cr, uid ,url, session, mage_attr_id, erp_attr_id, name, position='0' ,context=None):
		if context is None:
			context = {}
		if session:
			server = xmlrpclib.Server(url)
			options_data = {
						'label':[{'store_id':0, 'value':name}],
						'order':position,
						'is_default':0
					}
			try:
				mage_id = server.call(session, 'product_attribute.addOption', [mage_attr_id,options_data])
			except xmlrpclib.Fault, e:
				return [0,' Error in creating Option( %s ).%s'%(name,str(e))]
			if mage_id:
				self.pool.get('magento.product.attribute.value').create(cr, uid, {'name':erp_attr_id, 'erp_id':erp_attr_id, 'mage_id':mage_id, 'instance_id':context.get('instance_id'),})
				server.call(session, 'magerpsync.attributeoption_map', [{
															'name':name, 
															'mage_attribute_option_id':mage_id,
															'erp_attribute_option_id':erp_attr_id
														}])
				return [mage_id,'']

	def sync_template_attribute_set(self, cr, uid, ids, context=None):
		msg = ''
		success_ids = []
		fails_ids = []
		temp_pool = self.pool.get('product.template')
		mage_set_pool = self.pool.get('magento.attribute.set')
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			template_ids = temp_pool.search(cr, uid, [])
			for temp_id in template_ids:
				attribute_line_ids = temp_pool.browse(cr, uid, temp_id).attribute_line_ids
				attributes = []
				set_search1 = []
				default_search = mage_set_pool.search(cr, uid,[])
				if default_search:
					default_set = default_search[0]
				else:
					raise osv.except_osv(_('Information'), _("Default Attribute set not Found, please sync all Attribute set from Magento!!!"))
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
						temp_pool.write(cr, uid, temp_id, {'attribute_set_id':set_search1[0]}, context)			
						success_ids.append(temp_id)
					else:
						fails_ids.append(temp_id)
				else:
					temp_pool.write(cr, uid, temp_id, {'attribute_set_id':default_set}, context)
					success_ids.append(temp_id)
		if success_ids:
			msg = 'Magento Attribute Sets Successfully Assigned to following Product(s) %s.'%success_ids
		if fails_ids:
			msg += '\nFailed to attach attribute set in following Product(s) %s does not matched. Because Attribute Combination does not matched from any magento attribtue sets.'%fails_ids
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


	#############################################
	##    	Start Of Category Synchronizations ##
	#############################################


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
			instance_id = connection[2]
			context['instance_id'] = instance_id
			map_id = mage_cat_pool.search(cr,uid,[('instance_id','=',instance_id)])
			for m in map_id:
				map_obj = mage_cat_pool.browse(cr, uid, m)
				map_dic.append(map_obj.oe_category_id)
				catg_map[map_obj.oe_category_id] = map_obj.mag_category_id
			erp_catg = self.pool.get('product.category').search(cr,uid,[('name','!=','All products'),('id','not in',map_dic)], context=context)
			
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

	def sync_categories(self, cr, uid, url, session, cat_id, context):
		check = self.pool.get('magento.category').search(cr, uid, [('oe_category_id','=',cat_id),('instance_id','=',context.get('instance_id'))], context=context)		
		if not check:
			obj_catg = self.pool.get('product.category').browse(cr,uid,cat_id, context)
			name = obj_catg.name
			if obj_catg.parent_id.id:
				p_cat_id = self.sync_categories(cr, uid, url, session, obj_catg.parent_id.id, context)
			else:
				p_cat_id = self.create_category(cr, uid, url, session, cat_id, 1, name, context)
				return p_cat_id
			category_id = self.create_category(cr, uid, url, session, cat_id, p_cat_id, name, context)
			return category_id
		else:
			mage_id = self.pool.get('magento.category').browse(cr, uid, check[0]).mag_category_id
			return mage_id

	def create_category(self, cr, uid, url, session, catg_id, parent_id, catgname, context):
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
			##########  Mapping Entry  ###########
			category_array = {
								'cat_name':catg_id,
								'oe_category_id':catg_id,
								'mag_category_id':mage_cat,
								'created_by':'odoo',
								'instance_id':context.get('instance_id')
							}
			self.pool.get('magento.category').create(cr, uid, category_array)
			server.call(session, 'magerpsync.category_map', [{'mage_category_id':mage_cat,'erp_category_id':catg_id}])
			return mage_cat

	#############################################
	##    		Update All Categories  	   	   ##
	#############################################
	
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
			instance_id = connection[2]
			server = xmlrpclib.Server(url)
			map_id = self.pool.get('magento.category').search(cr,uid,[('need_sync','=','Yes'),('mag_category_id','!=',-1),('instance_id','=',instance_id)])

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
			context['instance_id'] = connection[2]
			for l in bulk_ids:
				search = map_pool.search(cr,uid,[('cat_name','=',l),('instance_id','=',context.get('instance_id'))])
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


	########## update specific category ##########
	def _update_specific_category(self, cr, uid, id, url, session, context):
		cat_mv = False
		get_category_data = {}
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
			move_data = [mage_id, mag_parent_id]
			try:
				server = xmlrpclib.Server(url)
				cat = server.call(session, 'catalog_category.update', update_data)
				cat_mv = server.call(session, 'catalog_category.move', move_data)
				self.pool.get('magento.category').write(cr, uid, id, {'need_sync':'No'}, context)
			except xmlrpclib.Fault, e:
				return [0, str(e)]
			except Exception, e:
				return [0, str(e)]
			return  [1, cat_id]	
	
	#############################################
	##    	End Of Category Synchronizations   ##
##########################################################
	
	

##########################################################
	##    	Start Of Product Synchronizations  ##
	#############################################


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
		map_dt = len(self.pool.get('magento.product.attribute').search(cr, uid, [], context=context))
		pro_op = len(self.pool.get('product.attribute.value').search(cr, uid, [], context=context))
		map_op = len(self.pool.get('magento.product.attribute.value').search(cr, uid, []))
		if pro_dt != map_dt or pro_op != map_op:
			raise osv.except_osv(('Warning'),_('Please, first map all ERP Product attributes and it\'s all options'))
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]
			instance_id = connection[2]
			context['instance_id'] = instance_id
			server = xmlrpclib.Server(url)			
			map_ids = map_tmpl_pool.search(cr,uid,[('instance_id','=',instance_id)])
			for map_id in map_ids:
				map_obj = map_tmpl_pool.browse(cr, uid, map_id)
				synced_ids.append(map_obj.erp_template_id)
			template_ids = self.pool.get('product.template').search(cr,uid,[('id', 'not in', synced_ids)], context=context)
			if not template_ids:
				raise osv.except_osv(_('Information'), _("No new product(s) Template found to be Sync."))
			if template_ids:
				for template_id in template_ids:
					response = self._export_specific_template(cr, uid, template_id, url, session, context)
					if response:
						if response[0] > 0:
							success_ids.append(template_id)
						else:
							error_ids.append(response[1])
			if success_ids:
				text = 'The Listed Product(s) %s has been successfully Synchronized to Magento. \n'%success_ids
			if error_ids:
				text1 = 'Error While Creating Listed Product(s) %s at Magento.'%error_ids
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
			context['instance_id'] = connection[2]
			for l in bulk_ids:
				search = map_obj.search(cr,uid,[('template_name','=',l),('instance_id','=',context.get('instance_id'))])	
				if not search:
					pro = self._export_specific_template(cr, uid, l, url, session, context)
					if pro:
						if pro[0] > 0:
							success_exp_ids.append(l)
						else:
							error_ids.append(pro[1])
				else :
					map_id = self.pool.get('magento.product.template').browse(cr, uid, search[0])
					if map_id.need_sync == 'Yes':
						pro_update = self._update_specific_product_template(cr, uid,  search[0], url, session, context)
						if pro_update:
							if pro_update[0] > 0:
								success_up_ids.append(pro_update[1])
							else:
								up_error_ids.append(pro_update[1])
					else:
						fail_ids.append(l)
			cr.commit()
			if success_exp_ids:
				text = "\nThe Listed Product(s) %s successfully created on Magento."%(success_exp_ids)
			if fail_ids:
				text += "\nSelected product(s) %s are already synchronized on magento."%(fail_ids)
			if error_ids:
				text += '\nThe Listed Product(s) %s does not synchronized on magento.'%error_ids
			if text:
				self.pool.get('magento.sync.history').create(cr, uid, {'status':'yes','action_on':'product','action':'b','error_message':text})
			if success_up_ids:
				text1 = '\nThe Listed Product(s) %s has been successfully updated to Magento. \n'%success_up_ids
				self.pool.get('magento.sync.history').create(cr, uid, {'status':'yes','action_on':'product','action':'c','error_message':text1})
			if up_error_ids:
				text2 = '\nThe Listed Product(s) %s does not updated on magento.'%up_error_ids
				self.pool.get('magento.sync.history').create(cr, uid, {'status':'no','action_on':'product','action':'c','error_message':text2})
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
	##    		Specific template sync	       ##
	#############################################
	def _export_specific_template(self, cr, uid, id, url, session, context):
		"""
		@param code: product Id.
		@param context: A standard dictionary
		@return: list
		"""		
		mage_set_id = 0
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
							search_ids = map_prod_pool.search(cr, uid, [('oe_product_id','=',vid),('instance_id','=',context.get('instance_id'))])
							if search_ids:
								map_obj = map_prod_pool.browse(cr, uid, search_ids[0])
								mage_variant_ids.append(map_obj.mag_product_id)						
							else:
								if single_value_dic:
									context = single_value_dic
								mage_ids = self._export_specific_product(cr, uid, vid, template_sku, url, session, context)
								if mage_ids and mage_ids[0]>0:
									mage_variant_ids.append(mage_ids[1])
						get_product_data['associated_product_ids'] = mage_variant_ids
						
					else:
						return [-1, str(id)+' Attribute Set Name not selected!!!']
				else :
					template_sku = 'single_variant'
					for obj in obj_pro.product_variant_ids:
						vid = obj.id
						search_ids = map_prod_pool.search(cr, uid, [('oe_product_id','=',vid),('instance_id','=',context.get('instance_id'))])
						if search_ids:
							map_obj = map_prod_pool.browse(cr, uid, search_ids[0])
							mage_variant_ids.append(map_obj.mag_product_id)
						else:
							mage_ids = self._export_specific_product(cr, uid, vid, template_sku, url, session, context)
							if mage_ids[0]>0:
								name  = obj_pro.name
								price = obj_pro.list_price or 0.0
								map_tmpl_pool.create(cr, uid, {'template_name':id, 'erp_template_id':id, 'mage_product_id':mage_ids[1], 'base_price':price, 'is_variants':False, 'instance_id':context.get('instance_id')})
							return mage_ids
			else:
				return [-2, str(id)+' No Variant Ids Found!!!']
			get_product_data['price_changes'] = mage_price_changes
			get_product_data['visibility'] = 4
			get_product_data['price'] = obj_pro.list_price or 0.00			
			get_product_data = self._get_product_array(cr, uid, url, session, obj_pro, get_product_data, context)			
			get_product_data['tax_class_id'] = '0'		
			if mage_set_id:
				newprod_data = ['configurable', mage_set_id, template_sku, get_product_data]
				self.pool.get('product.template').write(cr, uid, id, {'prod_type':'configurable'}, context)	
				try:
					mage_product_id = server.call(session, 'product.create', newprod_data)
				except xmlrpclib.Fault, e:
					return [0, str(id)+str(e)]
				if mage_product_id:
					server.call(session, 'product_stock.update', [mage_product_id,{'manage_stock':1,'is_in_stock':1}])
				map_tmpl_pool.create(cr, uid, {'template_name':id, 'erp_template_id':id, 'mage_product_id':mage_product_id, 'base_price': get_product_data['price'], 'is_variants':True, 'instance_id':context.get('instance_id')})
				server.call(session, 'magerpsync.template_map', [{'mage_template_id':mage_product_id,'erp_template_id':id}])
				if mage_product_id:
					self._create_product_attribute_media(cr, uid, url, session, obj_pro, mage_product_id)
				return [1,mage_product_id]
			else:
				return [-3, str(id)+' Attribute Set Name not found!!!']


	############# check single attribute lines ########
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

	############# fetch product details ########
	def _get_product_array(self, cr, uid, url, session, obj_pro, get_product_data, context):
		prod_catg = []
		for i in obj_pro.categ_ids:
			mage_categ_id = self.sync_categories(cr, uid, url, session, i.id, context)
			prod_catg.append(mage_categ_id)
		if obj_pro.categ_id.id:
			mage_categ_id = self.sync_categories(cr, uid, url, session, obj_pro.categ_id.id, context)
			prod_catg.append(mage_categ_id)
		status = 2
		if obj_pro.sale_ok:
			status = 1
		get_product_data['name'] = obj_pro.name
		get_product_data['short_description'] = obj_pro.description_sale or ' '
		get_product_data['description'] = obj_pro.description or ' '
		get_product_data['weight'] = obj_pro.weight_net or 0.00
		get_product_data['categories'] = prod_catg
		get_product_data['ean'] = obj_pro.ean13		
		get_product_data['status'] = status
		if not get_product_data.has_key('websites'):
			get_product_data['websites'] = [1]
		return get_product_data

	############# fetch product image ########
	def _create_product_attribute_media(self, cr, uid, url, session, obj_pro, mage_product_id):
		if obj_pro.image:
			server = xmlrpclib.Server(url)
			file = {'content':obj_pro.image,'mime':'image/jpeg'}
			type = ['image','small_image','thumbnail']
			pic = {'file':file,'label':'Label', 'position':'100','types':type, 'exclude':1}
			image = [mage_product_id,pic]
			if image:
				k = server.call(session,'catalog_product_attribute_media.create',image)			
				return True

	def _update_product_attribute_media(self, cr, uid, url, session, obj_pro, mage_product_id):
		if obj_pro.image:
			server = xmlrpclib.Server(url)
			file1 = ''
			pro_img_data = server.call(session,'catalog_product_attribute_media.list',[mage_product_id])			
			if pro_img_data:
				file1 = pro_img_data[0]['file']
				image_file = {'content':obj_pro.image,'mime':'image/jpeg'}			
				image_type = ['image','small_image','thumbnail']
				pic = {'file':image_file,'label':'Label', 'position':'100','types':image_type, 'exclude':1}
				image = [mage_product_id, file1, pic]
				if image:
					k = server.call(session,'catalog_product_attribute_media.update',image)
			else:
				self._create_product_attribute_media(cr, uid, url, session, obj_pro, mage_product_id)
			return True


	#############################################
	##    		Specific product sync	       ##
	#############################################
	def _export_specific_product(self, cr, uid, id, template_sku, url, session, context=None):
		"""
		@param code: product Id.
		@param context: A standard dictionary
		@return: list
		"""
		get_product_data = {}
		if context is None:
			context = {}		
		map_variant=[]		
		pro_attr_id = 0
		price_extra = 0
		mag_pro_pool = self.pool.get('magento.product')
		if id:
			obj_pro = self.pool.get('product.product').browse(cr, uid, id, context)			
			sku = obj_pro.default_code or 'Ref %s'%id
			if template_sku == sku:
				sku = 'Variant Ref %s'%id			
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
			get_product_data['price'] = obj_pro.list_price+price_extra or 0.00
			get_product_data = self._get_product_array(cr, uid, url, session, obj_pro, get_product_data, context)			
			get_product_data['tax_class_id'] = '0'
			if obj_pro.type in ['product','consu']:
				prodtype = 'simple'
			else:
				prodtype = 'virtual'	
			self.pool.get('product.product').write(cr, uid, id, {'prod_type':prodtype}, context)		
			pro = self.prodcreate(cr, uid, url, session, id, prodtype, sku, get_product_data, context)
			if pro and pro[0] != 0:
				self._create_product_attribute_media(cr, uid, url, session, obj_pro, pro[1])
			return pro

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
			server.call(session, 'product_stock.update', [pro,{'manage_stock':1,'qty':quantity,'is_in_stock':stock}])
			self.pool.get('magento.product').create(cr, uid, {'pro_name':pro_id,'oe_product_id':pro_id,'mag_product_id':pro,'instance_id':context.get('instance_id')})
			server.call(session, 'magerpsync.product_map', [{'mage_product_id':pro,'erp_product_id':pro_id}])
			return  [1, pro]


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
			instance_id = connection[2]
			server = xmlrpclib.Server(url)
			map_id = self.pool.get('magento.product.template').search(cr,uid,[('need_sync','=','Yes'),('instance_id','=',instance_id)])
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
	##    	update specific product template   ##
	#############################################
	def _update_specific_product_template(self, cr, uid, id, url, session, context):
		get_product_data = {}
		mage_variant_ids=[]
		mage_price_changes = {}
		server = xmlrpclib.Server(url)
		map_tmpl_pool = self.pool.get('magento.product.template')
		temp_obj = map_tmpl_pool.browse(cr, uid, id)
		temp_id = temp_obj.erp_template_id
		mage_id = temp_obj.mage_product_id
		if temp_id and mage_id:
			map_prod_pool = self.pool.get('magento.product')			
			obj_pro = self.pool.get('product.template').browse(cr, uid, temp_id, context)			
			get_product_data['price'] = obj_pro.list_price or 0.00
			get_product_data = self._get_product_array(cr, uid, url, session, obj_pro, get_product_data, context)			
			if obj_pro.product_variant_ids:
				if temp_obj.is_variants == True and obj_pro.is_product_variant == False:
					if obj_pro.attribute_line_ids :
						for obj in obj_pro.product_variant_ids:
							mage_update_ids = []
							vid = obj.id
							search_ids = map_prod_pool.search(cr, uid, [('oe_product_id','=',vid)])
							if search_ids:
								mage_update_ids = self._update_specific_product(cr, uid, search_ids[0], url, session, context)
				else:
					for obj in obj_pro.product_variant_ids:
						name  = obj_pro.name
						price = obj_pro.list_price or 0.0
						mage_update_ids = []
						vid = obj.id
						search_ids = map_prod_pool.search(cr, uid, [('oe_product_id','=',vid)])
						if search_ids:
							mage_update_ids = self._update_specific_product(cr, uid, search_ids[0], url, session, context=context)			
						if mage_update_ids and mage_update_ids[0]>0:
							map_tmpl_pool.write(cr, uid, id, {'need_sync':'No'}, context)
						return mage_update_ids
			else:
				return [-1, str(id)+' No Variant Ids Found!!!']
			update_data = [mage_id, get_product_data]
			try:
				temp = server.call(session, 'product.update', update_data)
				map_tmpl_pool.write(cr, uid, id, {'need_sync':'No'}, context)
			except xmlrpclib.Fault, e:
				return [0, str(temp_id)+str(e)]
			return [1, temp_id]

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
			quantity = 0
			stock = 0
			price_extra=0
			obj_pro = self.pool.get('product.product').browse(cr, uid, pro_id, context)
			if obj_pro.attribute_value_ids:
				for value_id in obj_pro.attribute_value_ids:
					get_product_data[value_id.attribute_id.name] = value_id.name
					pro_attr_id = value_id.attribute_id.id
					search_price_id = self.pool.get('product.attribute.price').search(cr, uid, [('product_tmpl_id','=',obj_pro.product_tmpl_id.id),('value_id','=',value_id.id)])
					if search_price_id:
						price_extra += self.pool.get('product.attribute.price').browse(cr,uid, search_price_id[0]).price_extra
			get_product_data['price'] = obj_pro.list_price+price_extra or 0.00
			get_product_data = self._get_product_array(cr, uid, url, session, obj_pro, get_product_data, context)
			update_data = [mage_id, get_product_data]
			try:
				pro = server.call(session, 'product.update', update_data)
				if mage_id:
					check = self._update_product_attribute_media(cr, uid, url, session, obj_pro, mage_id)
				
				
				self.pool.get('magento.product').write(cr, uid, id, {'need_sync':'No'}, context)
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

magento_synchronization()
# END