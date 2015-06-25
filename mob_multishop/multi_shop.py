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

class sale_order(osv.osv):
	_inherit = "sale.order"

	_columns = {     
			'wk_shop':fields.many2one('magento.store.view', 'Magento Store')
		}

sale_order()