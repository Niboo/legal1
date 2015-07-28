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
import logging
from openerp import models, fields, api, _

_logger = logging.getLogger(__name__)


class ProductImage(models.Model):
    _inherit = "product.template"

    @api.one
    @api.depends('image_ids')
    def _get_main_image(self):
        self.image = False
        self.image_medium = False
        self.image_small = False
        if self.image_ids:
            self.image = self.image_ids[0].image
            self.image_medium = self.image_ids[0].image_medium
            self.image_small = self.image_ids[0].image_small

    @api.one
    def _set_image(self):
        if self.image:
            if self.image_ids:
                self.image_ids[0].write({'image': self.image,
                    'name': self.main_image_name})
            else:
                self.image_ids = [(0, 0, {'image': self.image,
                                          'name': self.main_image_name or 'Main Image'})]
        elif self.image_ids:
            self.image_ids[0].unlink()

    @api.one
    def _set_image_medium(self):
        if self.image_medium:
            if self.image_ids:
                self.image_ids[0].write({'image': self.image_medium,
                    'name': self.main_image_name})
            else:
                self.image_ids = [(0, 0, {'image': self.image_medium,
                                          'name': self.main_image_name or 'Main Image'})]
        elif self.image_ids:
            self.image_ids[0].unlink()

    @api.one
    def _set_image_small(self):
        if self.image_small:
            if self.image_ids:
                self.image_ids[0].write({'image': self.image_small,
                    'name': self.main_image_name})
            else:
                self.image_ids = [(0, 0, {'image': self.image_small,
                                          'name': self.main_image_name or 'Main Image'})]
        elif self.image_ids:
            self.image_ids[0].unlink()

    @api.model
    def create(self, vals):
        if vals.get('mage_image_path'):
            vals['main_image_name'] = vals.get('mage_image_path').split('/')[-1]
        return super(ProductImage, self).create(vals)

    image_ids = fields.One2many(
        comodel_name='product.image', inverse_name='product_id',
        string='Product images', copy=True)
    image = fields.Binary(
        string="Main image", compute="_get_main_image", store=False,
        inverse="_set_image")
    image_medium = fields.Binary(
        compute="_get_main_image", inverse="_set_image_medium",
        store=False)
    image_small = fields.Binary(
        compute="_get_main_image", inverse="_set_image_small",
        store=False)
    main_image_name = fields.Char(string='Image title', required=True)
    @api.multi
    def write(self, vals):
        if 'image_medium' in vals and 'image_ids' in vals:
            # Inhibit the write of the image when images tab has been touched
            del vals['image_medium']
        return super(ProductImage, self).write(vals)


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_image_variant(self):
        self.image = False
        self.image_medium = False
        self.image_small = False
        if self.product_tmpl_id.image_ids:
            tmpl = self.product_tmpl_id.image_ids[0]
            own = self.product_tmpl_id.image_ids.filtered(
                    lambda r: r.variant_id.id == self.id)
            self.image = own and own[0].image or tmpl.image
            self.image_medium = own and own[0].image_medium or tmpl.image_medium
            self.image_small = own and own[0].image_small or tmpl.image_small

    @api.one
    def _set_image(self):
        tmpl = self.product_tmpl_id.image_ids
        own = self.product_tmpl_id.image_ids.filtered(
                lambda r: r.variant_id.id == self.id)
        if self.image:
            if own:
                own[0].write({'image': self.image,
                    'name': self.product_tmpl_id.main_image_name,
                    'variant_id': self.id,})
            elif tmpl:
                tmpl = [(0, 0, {'image': self.image,
                    'name': self.main_image_name or 'Main Image',
                    'variant_id': self.id,})]
            else:
                self.product_tmpl_id.image_ids = [(0, 0, {'image': self.image,
                    'name': self.main_image_name or 'Main Image'})]
        elif own:
            if own:
                own[0].unlink()
        elif tmpl:
            tmpl[0].unlink()

    @api.one
    def _set_image_medium(self):
        tmpl = self.product_tmpl_id.image_ids
        own = self.product_tmpl_id.image_ids.filtered(
                lambda r: r.variant_id.id == self.id)
        if self.image_medium:
            if own:
                own[0].write({'image': self.image_medium,
                    'name': self.product_tmpl_id.main_image_name,
                    'variant_id': self.id,})
            elif tmpl:
                tmpl = [(0, 0, {'image': self.image_medium,
                    'name': self.main_image_name or 'Main Image',
                    'variant_id': self.id,})]
            else:
                self.product_tmpl_id.image_ids = [(0, 0, {'image': self.image_medium,
                    'name': self.main_image_name or 'Main Image'})]
        elif own:
            if own:
                own[0].unlink()
        elif tmpl:
            tmpl[0].unlink()

    @api.one
    def _set_image_small(self):
        tmpl = self.product_tmpl_id.image_ids
        own = self.product_tmpl_id.image_ids.filtered(
                lambda r: r.variant_id.id == self.id)
        if self.image_small:
            if own:
                own[0].write({'image': self.image_small,
                    'name': self.product_tmpl_id.main_image_name,
                    'variant_id': self.id,})
            elif tmpl:
                tmpl = [(0, 0, {'image': self.image_small,
                    'name': self.main_image_name or 'Main Image',
                    'variant_id': self.id,})]
            else:
                self.product_tmpl_id.image_ids = [(0, 0, {'image': self.image_small,
                    'name': self.main_image_name or 'Main Image'})]
        elif own:
            if own:
                own[0].unlink()
        elif tmpl:
            tmpl[0].unlink()

    image = fields.Binary(
        string="Main image", compute="_get_image_variant", store=False,
        inverse="_set_image")
    image_medium = fields.Binary(
        compute="_get_image_variant", inverse="_set_image_medium",
        store=False)
    image_small = fields.Binary(
        compute="_get_image_variant", inverse="_set_image_small",
        store=False)

    @api.model
    def create(self, vals):
        if vals.get('mage_image_path'):
            vals['main_image_name'] = vals.get('mage_image_path').split('/')[-1]
        return super(ProductProduct, self).create(vals)
