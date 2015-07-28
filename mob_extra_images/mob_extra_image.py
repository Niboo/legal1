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
import xmlrpclib
import openerp.tools

XMLRPC_API = '/index.php/api/xmlrpc'


class mob_image_type(osv.osv):
    _name = 'mob.image.type'
    _columns = {
        'name':fields.char('Type')
    }
mob_image_type()


class product_image(osv.osv):
    _inherit = 'product.image'

    _columns = {
        'image_type':fields.many2many('mob.image.type','product_image_type','image_id', 'type_id','Image Type'),
        'mage_file' : fields.char('Magento File Name'),
        'mage_product_id' : fields.integer('Magento Product Id'),
    }

    _defaults = {
        'mage_product_id':0,
    }


class mob_extra_image(osv.osv):
    _name = 'mob.extra.image'

    def create_image(self, cr, uid, mage_product_id, product_id, product_type, image_list):
        img_pool = self.pool.get('product.image')
        pp_pool = self.pool.get('product.product')
        if product_id and product_type and mage_product_id:
            for data in image_list:
                if product_type == 'product':
                    pp_srch = pp_pool.search(cr,uid,[('id','=',product_id)])
                    data['product_id'] = pp_srch and pp_pool.browse(
                            cr,uid, pp_srch)[0].product_tmpl_id.id
                    data['variant_id'] = int(product_id)
                    min_seq = min([x.sequence for x in img_pool.search(
                        cr,uid,[('variant_id','=',product_id)])] + [99])
                else:
                    data['product_id'] = int(product_id)
                    min_seq = min([x.sequence for x in img_pool.search(
                        cr,uid,[('product_id','=',product_id)])] + [99])

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
                    data['sequence'] = min_seq - 1
                    if type_ids:
                        data['image_type'] = [(6, 0, type_ids)]
                data['mage_product_id'] = mage_product_id
                data['name'] = data.get('mage_file').split('/')[-1]
                img_search = img_pool.search(cr, uid, [('mage_file','=',data.get('mage_file')),('mage_product_id','=',mage_product_id)])
                if not img_search:
                    img_pool.create(cr, uid, data)
                else:
                    img_pool.write(cr, uid, img_search[0], data)
            return True
        return False

    def create_image_helper(self, cr, uid, vals):
        return self.create_image(
            cr,
            uid,
            vals.get('mage_product_id'),
            vals.get('product_id'),
            vals.get('product_type'),
            vals.get('image_list')
        )



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
        for i in obj_pro.image_ids:
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
        for i in obj_pro.image_ids:
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
