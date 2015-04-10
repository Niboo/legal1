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

XMLRPC_API = '/index.php/api/xmlrpc'

class magento_configure(osv.osv):
	_inherit = 'magento.configure'
	_columns = {
		'auto_image_del':fields.selection([('Yes','Yes'),('No','No')],'Auto Image Delete',required=True,help="If yes, then it'll delete corresponding magento images from products."),
	}
	_defaults={
		'auto_image_del':'No',
	}

	def _create_connection(self, cr, uid, context=None):
		""" create a connection between Odoo and magento 
			returns: False or list"""
		session = 0
		config_id = self.search(cr, uid, [('active','=',True)])
		if len(config_id) > 1:
			raise osv.except_osv(_('Error'), _("Sorry, only one Active Configuration setting is allowed."))
		if not config_id:
			raise osv.except_osv(_('Error'), _("Please create the configuration part for Magento connection!!!"))
		else:
			obj = self.browse(cr, uid, config_id[0])
			url = obj.name + XMLRPC_API
			user = obj.user
			pwd = obj.pwd
			auto_image = obj.auto_image_del
			if obj.language:
				context['lang'] = obj.language
			try:
				server = xmlrpclib.Server(url)
				session = server.login(user, pwd)
			except xmlrpclib.Fault, e:
				raise osv.except_osv(_('Error, %s')%e.faultString, _("Invalid Login Credentials!!!"))
			except IOError, e:
				raise osv.except_osv(_('Error'), _(" %s")% e)
			except Exception,e:
				raise osv.except_osv(_('Error'), _("Magento Connection Error in connecting: %s") % e)
			if session:
				return [url, session, auto_image]
			else:
				return False

magento_configure()

class product_template(osv.osv):
	_inherit = 'product.template'
	_columns = {	
		'tmpl_extra_image' : fields.many2many('mob.extra.image','tmp_img_set','tmpl_id','image_id','Extra Images')
	}

	def write(self, cr, uid, ids, vals, context=None):	
		res = super(product_template, self).write(cr, uid, ids, vals, context=context)
		if isinstance(ids, (int, long)):
			ids = [ids]
		if vals.has_key('tmpl_extra_image'):	
			for id in ids:
				image_ids = []
				self_obj = self.browse(cr, uid, id)
				line_ids = self_obj.attribute_line_ids.ids	
				vid = False
				if self_obj.product_variant_ids:
					vid = self_obj.product_variant_ids.ids[0] 	
				image_ids = self_obj.tmpl_extra_image.ids		
				if not line_ids and vid and image_ids:
					self.pool.get('product.product').write(cr, uid, vid, {'pro_extra_image':[(6, 0, image_ids )]})	
		return res

	def create(self, cr, uid, vals, context=None):	
		new_id = super(product_template, self).create(cr, uid, vals, context=context)
		self_obj = self.browse(cr, uid, new_id)
		line_ids = []
		if self_obj.attribute_line_ids:
			line_ids = self_obj.attribute_line_ids.ids	
		vid = False
		if self_obj.product_variant_ids:
			vid = self_obj.product_variant_ids.ids[0]
		image_ids = self_obj.tmpl_extra_image.ids		
		if not line_ids and vid and image_ids:
			self.pool.get('product.product').write(cr, uid, vid, {'pro_extra_image':[(6, 0, image_ids )]})	
		return new_id	

product_template()

class product_product(osv.osv):
	_inherit = 'product.product'
	_columns = {	
		'pro_extra_image' : fields.many2many('mob.extra.image','pro_img_set','pro_id','image_id','Extra Images')
	}

product_product()

class mob_image_type(osv.osv):
	_name = 'mob.image.type'
	_columns = {
		'name':fields.char('Type')
	}
mob_image_type()

class mob_extra_image(osv.osv):
	_name = 'mob.extra.image'

	_columns = {
		'name': fields.char('Label', size=64),
		'image': fields.binary("Image"),
		'image_type':fields.many2many('mob.image.type','product_image_type','image_id', 'type_id','Image Type'),
		'mage_file' : fields.char('Magento File Name'),
		'mage_product_id' : fields.integer('Magento Product Id'),
	}

	_defaults = {
		'mage_product_id':0,
	}

	def create_image(self, cr, uid, mage_product_id, product_id, product_type, image_list):
		img_ids = []		
		if product_id and product_type and mage_product_id:						
			for data in image_list:
				if data.has_key('types'):
					type_pool = self.pool.get('mob.image.type')
					types = data.get('types')
					type_ids = []
					for typ in types:
						search_type = type_pool.search(cr, uid, [('name','=',typ)])
						if search_type:
							type_ids.append(search_type[0])
						else:
							type_ids.append(type_pool.create(cr, uid, {'name':typ}))
					data.pop('types')
					if type_ids:
						data['image_type'] = [(6, 0, type_ids)]
				data['mage_product_id'] = mage_product_id
				img_search = self.search(cr, uid, [('mage_file','=',data.get('mage_file')),('mage_product_id','=',mage_product_id)])
				if not img_search:
					img_ids.append(self.create(cr, uid, data))
				else:
					img_ids.append(img_search[0])
			if img_ids:
				line_ids = []
				product_template_id = 0
				if product_type == 'product':
					product_template_id = self.pool.get('product.product').browse(cr, uid, product_id).product_tmpl_id.id 
					line_ids = self.pool.get('product.template').browse(cr, uid, product_template_id).attribute_line_ids.ids					
					if not line_ids and product_template_id:
						self.pool.get('product.template').write(cr, uid, product_template_id, {'tmpl_extra_image':[(6, 0, img_ids)]})
					else:
						self.pool.get('product.product').write(cr, uid, product_id, {'pro_extra_image':[(6, 0, img_ids )]})
				elif product_type == 'template':
					self.pool.get('product.template').write(cr, uid, product_id, {'tmpl_extra_image':[(6, 0, img_ids)]})
			return True
		return False

	def unlink(self, cr, uid, ids, context=None):
		if isinstance(ids, (int, long)):
			ids = [ids]
		connection = self.pool.get('magento.configure')._create_connection(cr, uid, context)
		if connection:
			url = connection[0]
			session = connection[1]
			auto_image = connection[2]
			if auto_image == 'Yes':
				server = xmlrpclib.Server(url)
				for id in ids:
					self_obj = self.browse(cr, uid, id)
					image_file = self_obj.mage_file or False
					mage_product_id = self_obj.mage_product_id or False
					if image_file and mage_product_id:
						try :
							server.call(session, 'product_media.remove', [mage_product_id, image_file])
						except Exception,e:
							pass
		return super(mob_extra_image, self).unlink(cr, uid, ids, context=context)

mob_extra_image()

class magento_synchronization(osv.osv):
	_inherit = 'magento.synchronization'

	#############################################
	##  Inherited export Specific product sync ##
	#############################################
	def _export_product_extra_images(self, cr, uid, id, pro, url, session, context=None):
		server = xmlrpclib.Server(url)
		obj_pro = self.pool.get('product.product').browse(cr, uid, id, context)	
		img_pool = self.pool.get('mob.extra.image')
		image_type_pool = self.pool.get('mob.image.type')	
		for i in obj_pro.pro_extra_image:			
			obj_img = img_pool.browse(cr, uid, i.id)
			position =str(100+i.id)
			files = {'content':obj_img.image,'mime':'image/jpeg'}
			types = []
			for img_id in obj_img.image_type.ids:
				types.append(image_type_pool.browse(cr, uid,img_id).name)
			pic = {'file':files,'label':obj_img.name, 'position':position, 'types':types, 'exclude':0}
			image = [pro[1],pic]
			k = server.call(session,'catalog_product_attribute_media.create',image)
			img_pool.write(cr, uid, [i.id], {'mage_file':k,'mage_product_id':pro[1]})
		return pro
		
	def _export_specific_product(self, cr, uid, id, template_sku, url, session, context=None):
		pro = super(magento_synchronization,self)._export_specific_product(cr, uid, id, template_sku, url, session, context)
		if pro and pro[0] != 0:
			self._export_product_extra_images(cr, uid, id, pro, url, session, context)
		return pro

	def _update_product_extra_images(self, cr, uid, pro_id, mage_id, url, session, context=None):
		server = xmlrpclib.Server(url)
		obj_pro = self.pool.get('product.product').browse(cr, uid, pro_id, context)
		image_type_pool = self.pool.get('mob.image.type')
		for i in obj_pro.pro_extra_image:
			img_pool = self.pool.get('mob.extra.image')
			obj_img = img_pool.browse(cr, uid, i.id, context)
			if not obj_img.mage_file :
				types = []
				position =str(100+i.id)
				files = {'content':obj_img.image,'mime':'image/jpeg'}	
				for img_id in obj_img.image_type.ids:
					types.append(image_type_pool.browse(cr, uid,img_id).name)			
				pic = {'file':files,'label':obj_img.name, 'position':position, 'types':types, 'exclude':0}
				image = [mage_id,pic]			
				k = server.call(session,'catalog_product_attribute_media.create',image)				
				img_pool.write(cr, uid, [i.id], {'mage_file':k,'mage_product_id':mage_id})
		return True


	def _update_specific_product(self, cr, uid, id, url, session, context=None):
		pro = super(magento_synchronization,self)._update_specific_product(cr, uid, id, url, session, context)
		if pro and pro[0]:
			server = xmlrpclib.Server(url)
			pro_obj = self.pool.get('magento.product').browse(cr, uid, id, context)
			pro_id = pro_obj.oe_product_id
			mage_id = pro_obj.mag_product_id
			######### update extra image #########		
			self._update_product_extra_images(cr, uid, pro_id, mage_id, url, session, context)
		return  pro
magento_synchronization()
