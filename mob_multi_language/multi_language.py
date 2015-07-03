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
import openerp.addons.decimal_precision as dp
import xmlrpclib
import openerp.tools

class language_mapping(osv.osv):
	_name = "language.mapping"
	_description = "Language Mapping"
	_columns = {
		'name':fields.char('Language Code', size=64),
		'mage_store_id':fields.integer('Magento Store Id'),
		'instance_id' :fields.many2one('magento.configure','Magento Instance'),
		'create_date':fields.datetime('Created Date', readonly=True),
	}
language_mapping()

class magento_synchronization(osv.osv):
	_inherit = 'magento.synchronization'

	#############################################
	##  Inherited export Specific product sync ##
	#############################################

	def _update_product_translations(self, cr, uid, pro_id, mage_id, url, session, context=None):
		if context == None:
		    context = {}
		response = False
		product_data = {}
		server = xmlrpclib.Server(url)
		product_pool = self.pool.get('product.product')
		language_pool = self.pool.get('language.mapping')
		mapping_ids = language_pool.search(cr, uid, [('instance_id','=',context.get('instance_id'))])
		for mapping_id in mapping_ids:
			language_obj = language_pool.browse(cr, uid, mapping_id)
			context['lang'] = language_obj.name
			store_id = language_obj.mage_store_id
			if store_id:
				product_obj = product_pool.browse(cr, uid, pro_id, context)
				product_data['name'] = product_obj.name
				product_data['description'] = product_obj.description
				product_data['short_description'] = product_obj.description_sale
				try:
					update_data = [mage_id, product_data, store_id]
					pro = server.call(session, 'product.update', update_data)
					response = True
				except xmlrpclib.Fault, e:
					response = False
		return response

	def _export_specific_product(self, cr, uid, id, template_sku, url, session, context=None):
		pro = super(magento_synchronization,self)._export_specific_product(cr, uid, id, template_sku, url, session, context)
		if pro and pro[0] != 0:
			######### Update Variant Transaltion #########
			self._update_product_translations(cr, uid, id, pro, url, session, context)
		return pro

	def _update_specific_product(self, cr, uid, id, url, session, context=None):
		pro = super(magento_synchronization,self)._update_specific_product(cr, uid, id, url, session, context)
		if pro and pro[0]:
			pro_obj = self.pool.get('magento.product').browse(cr, uid, id, context)
			pro_id = pro_obj.oe_product_id
			mage_id = pro_obj.mag_product_id
			######### Update Variant Transaltion #########
			self._update_product_translations(cr, uid, pro_id, mage_id, url, session, context)
		return  pro

magento_synchronization()