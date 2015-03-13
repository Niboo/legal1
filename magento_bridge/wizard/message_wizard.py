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

	
class message_wizard(osv.osv_memory):
	_name = "message.wizard"
	_columns={
			'text': fields.text('Message' ,readonly=True ,translate=True),
	         }
message_wizard()

class region_wizard(osv.osv_memory):
	_name = "region.wizard"	
	_columns={
		'country_ids': fields.many2one('res.country', 'Country'),
	}
	
	def _sync_mage_region(self, cr, uid, url, session, country_code, context=None):		
		list = {}
		dict = {}
		server = xmlrpclib.Server(url)
		try:
			regions=server.call(session, 'region.list',[country_code])
		except xmlrpclib.Fault, e:
			raise osv.except_osv(_('Error'), _(" %s")% e)			
		if regions:
			for i in regions:
				list['name'] = i['name']
				list['region_code'] = i['code']
				list['country_code'] = country_code								
				list['mag_region_id'] = i['region_id']	
				self.pool.get('magento.region').create(cr,uid,list)
				if country_code != 'US':
					country_ids = self.pool.get('res.country').search(cr, uid,[('code','=',country_code)])
					dict['name'] = i['name']
					dict['country_id'] = country_ids[0]
					dict['code'] = i['name'][:2].upper()				
					self.pool.get('res.country.state').create(cr,uid,dict)
					
			return len(regions)
		else:
			return 0;
	
	def sync_state(self,cr,uid,ids,context=None):		
		config_id=self.pool.get('magento.configure').search(cr,uid,[('active','=',True)])		
		if len(config_id)>1:
			raise osv.except_osv(_('Error'), _("Sorry, only one Active Configuration setting is allowed."))
		if not config_id:
			raise osv.except_osv(_('Error'), _("Please create the configuration part for connection!!!"))
		else:
			obj = self.pool.get('magento.configure').browse(cr,uid,config_id[0])
			url = obj.name+'/index.php/api/xmlrpc'
			user = obj.user
			pwd = obj.pwd
			try:
				server = xmlrpclib.Server(url)
				session = server.login(user,pwd)
			except xmlrpclib.Fault, e:
				raise osv.except_osv(_('Error %s')%e, _("Invalid Information"))
			except IOError, e:
				raise osv.except_osv(_('Error'), _(" %s")% e)
			except Exception,e:
				raise osv.except_osv(_('Error'), _("Magento Connection " + netsvc.LOG_ERROR +  " in connecting: %s") % e)
			if session:
				country_id = self.browse(cr, uid, ids[0]).country_ids
				country_code = self.pool.get('res.country').browse(cr, uid, country_id.id).code
				map_id = self.pool.get('magento.region').search(cr,uid,[('country_code','=',country_code)])
				if not map_id:
					total_regions=self._sync_mage_region(cr, uid, url, session, country_code)
					if total_regions == 0:
						raise osv.except_osv(_('Error'), _("There is no any region exist for country %s.")%(country_id.name))
						return {
						'type': 'ir.actions.act_window_close',
						}
					else:
						text="%s Region of %s are sucessfully Imported to OpenERP."%(total_regions,country_id.name)
						partial = self.pool.get('message.wizard').create(cr, uid, {'text':text}, context)
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
				else:
					raise osv.except_osv(_('Information'), _("All regions of %s are already imported to OpenERP.")%(country_id.name))
region_wizard()