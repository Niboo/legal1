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

class magento_store_view(osv.osv):
	_inherit = "magento.store.view"

	def sync_store_view(self, cr, uid, store_data, context=None):
		if context is None:
			context = {}
		store_id = self._get_store_view(cr, uid, store_data, context)
		return store_id



class product_template(osv.osv):
	_inherit = "product.template"

	_columns = {
        'wk_websites_id': fields.many2many('magento.website','wk_website_rel','store_id','group_id','Websites'),
	}

	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		website_ids = []
		if context.has_key('magento') and vals.has_key('wk_websites_id'):
			website_ids = self.pool.get('magento.website').search(cr, uid, [('website_id','in',vals['wk_websites_id']),('instance_id','=',context.get('instance_id'))])
			if website_ids:
				vals['wk_websites_id'] = [(6, 0, website_ids)]
		return super(product_template, self).create(cr, uid, vals, context=context)

	def write(self, cr, uid, ids, vals, context=None):
		if context is None:
			context = {}
		website_ids = []
		if context.has_key('magento') and vals.has_key('wk_websites_id'):
			website_ids = self.pool.get('magento.website').search(cr, uid, [('website_id','in',vals['wk_websites_id']),('instance_id','=',context.get('instance_id'))])
			if website_ids:
				vals['wk_websites_id'] = [(6, 0, website_ids)]
		res = super(product_template, self).write(cr, uid, ids, vals, context=context)
		return res

class sale_order(osv.osv):
	_inherit = "sale.order"

	_columns = {     
			'wk_shop':fields.many2one('magento.store.view', 'Magento Store')
		}

class magento_synchronization(osv.osv):
	_inherit = "magento.synchronization"

	def _get_product_array(self, cr, uid, url, session, obj_pro, get_product_data, context):
		website_ids = []
		for website_id in obj_pro.wk_websites_id:			
			website_ids.append(website_id.website_id)		
		get_product_data['websites'] = website_ids
		return super(magento_synchronization, self)._get_product_array(cr, uid, url, session, obj_pro, get_product_data, context)

sale_order()