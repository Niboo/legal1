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
import openerp.netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import datetime
import xmlrpclib

################## .............magento-openerp stock.............##################

class product_template(osv.osv):
	_inherit = "product.template"
	_columns = {
		'attributes':fields.one2many('product.attributes','fkey_product','Custom Attributes'),
		'custom_options':fields.one2many('product.custom.options','fkey2_product','Custom Options'),
	}
product_template()	

class product_custom_options(osv.osv):
	_name = "product.custom.options"
	_description = "Magento Custom Options"
	_order = 'id desc'
	_columns = {
		'name': fields.char('Title' ,size=100 ),
		'values': fields.char('Values' ,size=100 ),
		'mage_id': fields.integer('Magento Option Id' ,size=100 ),
		'create_date': fields.datetime('Created Date'),
		'write_date': fields.datetime('Updated Date'),
		'fkey2_product':fields.many2one('product.template','Product'),
	}
	def _balance_custom_options(self, cr, uid, current_options, tmpl_id, context=None):
		previous_options = []
		search_ids = self.search(cr, uid, [('fkey2_product','=',tmpl_id)])
		if search_ids:
			for i in search_ids:
				obj = self.browse(cr, uid, i)
				previous_options.append((i,obj.mage_id))
		unlink_options = list(set(previous_options) - set(current_options))
		if unlink_options:
			for u in unlink_options:
				self.unlink(cr, uid, u[0])
		return True
		
	def link_product_with_custom_options(self, cr, uid, data, product_id, context=None):
		custom_list = {}
		current_options = []
		tmpl_id = self.pool.get('product.product').browse(cr, uid, product_id).product_tmpl_id.id
		for d in data:
			custom_list['mage_id'] = opt_id = d['option_id']
			custom_list['name'] = title = d['title']
			custom_list['values'] = values = d['values']
			custom_list['fkey2_product'] = tmpl_id
			opt = self.search(cr, uid, [('fkey2_product','=',tmpl_id),('mage_id','=',opt_id)])
			if not opt:
				id = self.create(cr, uid, custom_list)
			else:
				id = opt[0]
				created_values = self.browse(cr, uid, id).values
				if created_values != values:
					self.write(cr, uid, id, {'values':values})
			current_options.append((id,opt_id))
		self._balance_custom_options(cr, uid, current_options, tmpl_id)
		return True
		
class product_attributes(osv.osv):
	_name = "product.attributes"
	_description = "Magento Product Custom Attributes"
	_order = 'id desc'	
	def _has_media(self, cr, uid, ids, name, args, context=None):
		result = {}
		for obj in self.browse(cr, uid, ids, context=context):
			result[obj.id] = obj.image != False
		return result

	_columns = {
		'name': fields.char('Name' ,size=100 ),
		'attribute_id': fields.many2one('magento.attributes','Attribute'),
		'value': fields.char('Value' ,size=100 ),
		'image': fields.binary('Media Image'),
		'has_media': fields.function(_has_media, type="boolean" ),
		'create_date': fields.datetime('Created Date'),
		'write_date': fields.datetime('Updated Date'),
		'fkey_product':fields.many2one('product.template','Product'),
	}
	
	def link_product_attributes(self, cr, uid, data, context=None):
		attr_list = {}
		value = False		
		tmpl_id = 0
		mage_attribute_id = 0
		input_type = data.get('input_type')
		if data.has_key('attribute_id'):
			mage_attribute_id = data['attribute_id']
		if data.has_key('product_id'):
			tmpl_id = self.pool.get('product.product').browse(cr, uid, data.get('product_id')).product_tmpl_id.id
			attr_list['fkey_product'] = tmpl_id
		if data.has_key('value'):
			value = data['value']
		if value and input_type == 'media_image':
			attr_list['image'] = value
		elif value:
			attr_list['value'] = value
		if mage_attribute_id :
			attribute_id = self.pool.get('magento.attributes').search(cr,uid,[('mage_id','=',mage_attribute_id),('instance_id','=',context.get('instance_id'))])
			if attribute_id and tmpl_id:
				search_id = self.search(cr,uid,[('attribute_id','=',attribute_id[0]),('fkey_product','=',tmpl_id)])
				if search_id:
					if not value:
						self.unlink(cr, uid, search_id[0])
					elif input_type == 'media_image':
						self.write(cr, uid, search_id[0], {'image':value})
					else:
						attr_value = self.browse(cr, uid, search_id[0]).value
						if value != attr_value:
							self.write(cr, uid, search_id[0], {'value':value})
				if not search_id and value:
					attr_list['attribute_id'] = attribute_id[0]
					self.create(cr, uid, attr_list)
				return True
		return False

class magento_attributes(osv.osv):
	_name = "magento.attributes"
	_description = "Magento Custom Attributes"
	_order = 'id desc'
	_rec_name = 'label'
	_columns = {
		'name': fields.char('Attribute code' ,size=100 ),
		'label': fields.char('Label' ,size=100 ),
		'mage_id': fields.integer('Magento Attribute Id' ,size=100 ),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'create_date': fields.datetime('Created Date'),
		'write_date': fields.datetime('Updated Date'),
	}
magento_attributes()
