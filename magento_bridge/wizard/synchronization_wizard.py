# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc


class synchronization_wizard(osv.osv_memory):
	_name = 'synchronization.wizard'

	_columns = {
		'action': fields.selection([('export','Export'),('update','Update')],'Action',required=True, help="""Export: Export all Odoo Category/Products at Magento. Update: Update all synced products/categories at magento, which requires to be update at magento"""),
	}

	_defaults={
		'action': 'export',
	}
	def start_category_synchronization(self, cr, uid, ids, context=None):		
		if context is None:
			context = {}
		message = ''
		for wiz_id in ids:
			sync_obj = self.browse(cr, uid, wiz_id)
		if sync_obj.action == 'export':
			message = self.pool.get('magento.synchronization').export_categories(cr, uid, context.get('active_ids'), context)
		else:
			message = self.pool.get('magento.synchronization').update_categories(cr, uid, context.get('active_ids'), context)

		return message

	def start_product_synchronization(self, cr, uid, ids, context=None):		
		if context is None:
			context = {}

		message = ''
		for i in ids:
			sync_obj = self.browse(cr,uid,i)
		if sync_obj.action == 'export':
			message = self.pool.get('magento.synchronization').export_products(cr, uid, context.get('active_ids'), context)
		else:
			message = self.pool.get('magento.synchronization').update_products(cr, uid, context.get('active_ids'), context)

		return message

	def start_product_template_synchronization(self, cr, uid, ids,context=None):		
		if context is None:
			context = {}

		message = self.pool.get('magento.synchronization').export_bulk_product_template(cr, uid, context)

		return message

	def start_category_template_synchronization(self, cr, uid, ids,context=None):		
		if context is None:
			context = {}

		message = self.pool.get('magento.synchronization').export_bulk_category(cr, uid, context)

		return message

	def start_bulk_product_synchronization(self, cr, uid, context=None):
		partial = self.create(cr, uid, {}, context)
		#raise osv.except_osv(('c'),('Che'))
		context['bulk'] = False
		return { 'name':_("Synchronization Bulk Product"),
				 'view_mode': 'form',
				 'view_id': False,
				 'view_type': 'form',
				'res_model': 'synchronization.wizard',
				 'res_id': partial,
				 'type': 'ir.actions.act_window',
				 'nodestroy': True,
				 'target': 'new',
				 'context': context,
				 'domain': '[]',
			}

	def start_bulk_category_synchronization(self, cr, uid, context=None):		
		partial = self.create(cr, uid, {}, context)
		context['category'] = False
		return { 'name':_("Synchronization Bulk Category"),
				 'view_mode': 'form',
				 'view_id': False,
				 'view_type': 'form',
				'res_model': 'synchronization.wizard',
				 'res_id': partial,
				 'type': 'ir.actions.act_window',
				 'nodestroy': True,
				 'target': 'new',
				 'context':context,
				 'domain': '[]',
			}

synchronization_wizard()