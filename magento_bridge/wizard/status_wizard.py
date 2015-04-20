 # -*- coding: utf-8 -*-
##############################################################################
#		
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import tools
import time
import openerp.pooler
import openerp.netsvc
import xmlrpclib
from datetime import date

	
	######################## Mapping update Model(Used from server action) #########################
	
class mapping_update(osv.osv_memory):
	_name = "mapping.update"
	_columns={
		'need_sync':fields.selection([('Yes', 'Yes'),('No', 'No')],'Update Required'),
	}
	
	def open_update_wizard(self, cr, uid, context=None):		
		partial = self.create(cr, uid, {}, context)
		return { 'name':_("Bulk Action"),
				 'view_mode': 'form',
				 'view_id': False,
				 'view_type': 'form',
				'res_model': 'mapping.update',
				 'res_id': partial,
				 'type': 'ir.actions.act_window',
				 'nodestroy': True,
				 'target': 'new',
				 'context':context,
				 'domain': '[]',
			}

	def update_mapping_status(self, cr, uid, ids, context=None):
		count = 0
		model = context.get('active_model')
		active_ids = context.get('active_ids')
		status = self.browse(cr, uid, ids[0]).need_sync
		for i in active_ids:
			self.pool.get(model).write(cr, uid, i, {'need_sync':status})
			count = count+1
		text = 'Status of %s record has been successfully updated to %s.'%(count,status)
		partial = self.pool.get('message.wizard').create(cr, uid, {'text':text}, context)
		return { 'name':_("Information"),
				 'view_mode': 'form',
				 'view_id': False,
				 'view_type': 'form',
				'res_model': 'message.wizard',
				 'res_id': partial,
				 'type': 'ir.actions.act_window',
				 'nodestroy': True,
				 'target': 'new',
			 }
		
mapping_update()