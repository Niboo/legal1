# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Odoo Source Management Solution
#    Copyright (c) 2014 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
import os
import base64
import urllib
import logging

from shutil import copyfile

from openerp import models, fields, api, exceptions, _
from openerp import tools

_logger = logging.getLogger(__name__)


class ProductImage(models.Model):
    _name = "product.image"

    @api.one
    def copy(self, default=None):
        new_id = super(ProductImage, self).copy(default)

        new_image = self.browse(new_id)

        old_path = self._image_path()
        new_path = new_image._image_path()
        old_medium = self._medium_path()
        new_medium = new_image._medium_path()
        old_thumb = self._thumb_path()
        new_thumb = new_image._thumb_path()

        new_image._check_filestore()

        try:
            copyfile(old_path, new_path)
            copyfile(old_medium, new_medium)
            copyfile(old_thumb, new_thumb)
        except Exception, e:
            _logger.error("Can not open the image %s, error : %s",
                    old_path, e, exc_info=True)

            return new_id

    @api.multi
    def unlink(self):
        for image in self:
            full_path = image._image_path()
            if full_path:
                os.path.isfile(full_path) and os.remove(full_path)
            medium_path = self._medium_path()
            if medium_path:
                os.path.isfile(medium_path) and os.remove(medium_path)
            thumb_path = self._thumb_path()
            if thumb_path:
                os.path.isfile(thumb_path) and os.remove(thumb_path)
        return super(ProductImage, self).unlink()

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            for image in self:
                old_full_path = image._image_path()
                old_thumb_path = image._thumb_path()
                old_medium_path = image._medium_path()
                if not old_full_path:
                    continue
                # all the stuff below is there to manage the files on the filesystem
                if vals.get('name') and (image.name != vals['name']):
                    new_image = super(ProductImage, image).write(vals)
                    if 'image' in vals:
                        # a new image have been loaded we should remove the old image
                        if os.path.isfile(old_full_path):
                            os.remove(old_full_path)
                        if os.path.isfile(old_medium_path):
                            os.remove(old_medium_path)
                        if os.path.isfile(old_thumb_path):
                            os.remove(old_thumb_path)
                    else:
                        new_full_path = image._image_path()
                        new_medium_path = image._medium_path()
                        new_thumb_path = image._thumb_path()
                        #we have to rename the image on the file system
                        if os.path.isfile(old_full_path):
                            os.rename(old_full_path, new_full_path)
                        if os.path.isfile(old_medium_path):
                            os.rename(old_medium_path, new_medium_path)
                        if os.path.isfile(old_thumb_path):
                            os.rename(old_thumb_path, new_thumb_path)
        return super(ProductImage, self).write(vals)

    @api.multi
    def _image_path(self):
        self.ensure_one()
        full_path = False
        local_media_repository = self.env['res.company'].get_local_media_repository()
        if local_media_repository:
            full_path = os.path.join(
                    local_media_repository,
                    str(self.product_id.id),
                    '%s' % (self.name or ''))
            return full_path

    @api.multi
    def _medium_path(self):
        self.ensure_one()
        full_path = False
        local_media_repository = self.env['res.company'].get_local_media_repository()
        if local_media_repository:
            full_path = os.path.join(
                    local_media_repository,
                    str(self.product_id.id),
                    'mediums',
                    '%s' % (self.name or ''))
            return full_path

    @api.multi
    def _thumb_path(self):
        self.ensure_one()
        full_path = False
        local_media_repository = self.env['res.company'].get_local_media_repository()
        if local_media_repository:
            full_path = os.path.join(
                    local_media_repository,
                    str(self.product_id.id),
                    'thumbs',
                    '%s' % (self.name or ''))
            return full_path

    @api.one
    def get_image(self):
        try:
            full_path = self._image_path()
        except Exception, e:
            _logger.error("Can not find the path for image %s: %s", id, e, exc_info=True)
            return False
        if not full_path:
            raise osv.except_osv(_('Error'),
                    _('Company must be configure first for image display'))
        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    img = base64.b64encode(f.read())
            except Exception, e:
                _logger.error("Can not open the image %s, error : %s",
                        full_path, e, exc_info=True)
                return False
        else:
            _logger.error("The image %s doesn't exist ", full_path)
            return False
        return img

    @api.one
    def get_medium(self):
        try:
            full_path = self._medium_path()
        except Exception, e:
            _logger.error("Can not find the path for thumb %s: %s", id, e, exc_info=True)
            return False
        if not full_path:
            raise osv.except_osv(_('Error'),
                    _('Company must be configure first for image display'))

        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    img = base64.b64encode(f.read())
            except Exception, e:
                _logger.error("Can not open the thumb %s, error : %s",
                        full_path, e, exc_info=True)
                return False
        else:
            _logger.error("The thumb %s doesn't exist ", full_path)
            return False
        return img

    @api.one
    def get_thumb(self):
        try:
            full_path = self._thumb_path()
        except Exception, e:
            _logger.error("Can not find the path for thumb %s: %s", id, e, exc_info=True)
            return False
        if not full_path:
            raise osv.except_osv(_('Error'),
                    _('Company must be configure first for image display'))

        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    img = base64.b64encode(f.read())
            except Exception, e:
                _logger.error("Can not open the thumb %s, error : %s",
                        full_path, e, exc_info=True)
                return False
        else:
            _logger.error("The thumb %s doesn't exist ", full_path)
            return False
        return img

    @api.one
    def _get_image(self):
        user = self.env['res.users'].browse(self._uid)
        img = self.with_context(lang=user.lang, bin_size=False)
        self.image = img.get_image()
        self.image_medium = img.get_medium()
        self.image_small = img.get_thumb()

    @api.one
    def _save_file(self, image=False):
        """Save a file encoded in base 64"""
        self._check_filestore()
        img = image or self.image
        with open(self._image_path(), 'w') as ofile:
            try:
                ofile.write(base64.b64decode(img))
            except:
                pass
        with open(self._medium_path(), 'w') as ofile:
            try:
                ofile.write(base64.b64decode(tools.image_resize_image_medium(img)))
            except:
                pass
        with open(self._thumb_path(), 'w') as ofile:
            try:
                ofile.write(base64.b64decode(tools.image_resize_image_small(img)))
            except:
                pass
        return True

    @api.multi
    def _check_filestore(self):
        """check if the filestore is created, and do it otherwise."""
        for product_image in self:
            dir_path = os.path.dirname(product_image._image_path())
            medium_path = os.path.dirname(product_image._medium_path())
            thumb_path = os.path.dirname(product_image._thumb_path())
            try:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                if not os.path.exists(medium_path):
                    os.makedirs(medium_path)
                if not os.path.exists(thumb_path):
                    os.makedirs(thumb_path)
            except OSError, e:
                raise exceptions.Warning(
                        _('The image filestore can not be created, %s') % e)
        return True

    @api.one
    def _set_image(self):
        user = self.env['res.users'].browse(self._uid)
        img = self.with_context(lang=user.lang)
        image = self.image
        full_path = img._image_path()
        if not full_path:
            raise osv.except_osv(_('Error'),
                _('Product Images needs to be configured first in company'))
        img._save_file(image)

    sequence = fields.Integer(string='Sequence', default=999)
    name = fields.Char(string='Image title', required=True)
    image = fields.Binary(
            compute="_get_image", inverse="_set_image", string="File")
    image_medium = fields.Binary(
            compute="_get_image", string="Medium-sized image",
            help="Medium-sized image. It is automatically resized as a 128 x "
            "128 px image, with aspect ratio preserved, only when the image "
            "exceeds one of those sizes. Use this field in form views or "
            "some kanban views.")
    image_small = fields.Binary(
            compute="_get_image", string="Small-sized image",
            help="Small-sized image. It is automatically resized as a 64 x 64 px "
            "image, with aspect ratio preserved. Use this field anywhere a "
            "small image is required.")
    comments = fields.Text(string='Comments')
    product_id = fields.Many2one(
            comodel_name='product.template', string='Product', required=True,
            ondelete='cascade')
    variant_id = fields.Many2one(
            comodel_name='product.product', string='Variant', required=False,
            ondelete='cascade')

    # converted from mob_extra_images
    image_type = fields.Many2many(
        comodel_name='product.image.type',
        relation='product_img_to_img_type',
        column1='image_id',
        column2='type_id',
        string='Image Type'
    )
    mage_file = fields.Char('Magento File Name')
    mage_product_id = fields.Integer('Magento product ID', default=0)

    @api.model
    def create_image(self, mage_product_id, product_id, product_type, image_list):
        type_env = self.env['product.image.type']
        if product_id:
            tmpl_id = product_id
            if product_type == 'product':
                tmpl_id = self.env['product.product'].search([('id','=',product_id)])[0].product_tmpl_id.id
            else:
                product_id = None

            for data in image_list:
                image = self.search([('mage_file','=',data.get('mage_file')),
                    ('mage_product_id','=',mage_product_id)
                    ])
                data['name'] = (data.get('mage_file','default.jpg')).rpartition('/')[-1]
                data['product_id'] = tmpl_id
                data['variant_id'] = product_id
                type_ids = []
                for typ in data.get('types', []):
                    if typ:
                        search_type = type_env.search([('name','=',typ)])
                        if search_type:
                            type_ids.append(search_type[0])
                        else:
                            type_ids.append(type_env.create({'name':typ}))
                data.pop('types')
                image_data = data.get('image')
                if type_ids:
                    data['image_type'] = [(6, 0, [x.id for x in type_ids])]
                    data['sequence'] = 0
                    if image:
                        image.sequence = 0
                        image.image_type = [(6, 0, [x.id for x in type_ids])]
                else:
                    if image:
                        image.sequence = 999
                        image.image_type = [(6,0,[])]
                if not image:
                    new_image = self.create(data)
                    new_image.image = image_data

    @api.model
    def create_image_helper(self, vals):
        return self.create_image(
                vals.get('mage_product_id'),
                vals.get('product_id'),
                vals.get('product_type'),
                vals.get('image_list')
            )

    _order = 'product_id desc, sequence, id'

    _sql_constraints = [
            ('uniq_name_product_id', 'UNIQUE(product_id, name)',
                _('A product can have only one image with the same name')),
            ]


class ProductImageType(models.Model):
    _name = 'product.image.type'
    name = fields.Char('Type')
