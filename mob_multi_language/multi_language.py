# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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

	##############################################
	##  Inherited export Specific category sync ##
	##############################################

	def _update_cateogry_translations(self, cr, uid, cat_id, mage_id, url, session, context=None):
		if context == None:
		    context = {}
		response = False
		category_data = {}
		server = xmlrpclib.Server(url)
		category_pool = self.pool.get('product.category')
		language_pool = self.pool.get('language.mapping')
		mapping_ids = language_pool.search(cr, uid, [('instance_id','=',context.get('instance_id'))])
		for mapping_id in mapping_ids:
			language_obj = language_pool.browse(cr, uid, mapping_id)
			context['lang'] = language_obj.name
			store_id = language_obj.mage_store_id
			if store_id:
				category_obj = category_pool.browse(cr, uid, cat_id, context)
				category_data['name'] = category_obj.name
				try:
					update_data = [mage_id, category_data, store_id]
					cat = server.call(session, 'category.update', update_data)
					response = True
				except xmlrpclib.Fault, e:
					response = False
		return response

	def sync_categories(self, cr, uid, url, session, cat_id, context):
		cat = super(magento_synchronization,self).sync_categories(cr, uid, url, session, cat_id, context)
		if cat and cat[0] != 0:
			######### Update Variant Transaltion #########
			self._update_cateogry_translations(cr, uid, cat_id, cat, url, session, context)
		return cat

	def _update_specific_category(self, cr, uid, id, url, session, context):
		cat = super(magento_synchronization,self)._update_specific_category(cr, uid, id, url, session, context)
		if cat and cat[0]:
			cat_obj = self.pool.get('magento.category').browse(cr, uid, id, context)
			cat_id = cat_obj.oe_category_id
			mage_id = cat_obj.mag_category_id
			######### Update Variant Transaltion #########
			self._update_cateogry_translations(cr, uid, cat_id, mage_id, url, session, context)
		return cat

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