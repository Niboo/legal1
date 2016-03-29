# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Jerome Guerriat
#    Copyright 2015 Niboo SPRL
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

from openerp import http
from openerp import exceptions


class InboundController(http.Controller):
    @http.route('/inbound_screen', type='http', auth="user")
    def inbound_screen(self, **kw):
        inbound_suppliers  = http.request.env['res.partner'].search(
            [('is_in_inbound','=',True)]
            ,order='sequence'
        )

        return http.request.render('stock_irm.inbound_screen', {
              'suppliers': inbound_suppliers,
        })

    @http.route('/inbound_screen/get_suppliers', type='json', auth="user")
    def get_suppliers(self, search="",  **kw):
        env = http.request.env
        inbound_suppliers = list()

        domain = [('is_in_inbound','=',True)]

        if search:
            domain.append(('display_name','ilike',search))

        suppliers = env['res.partner'].search(
            domain,
            order='sequence'
        )

        for supplier in suppliers:
            inbound_suppliers.append({
                'id': supplier.id,
                'name': supplier.name,
                'image': "/web/binary/image?model=res.partner&id=%s&field=image" % supplier.id
            })
        results = {'status': 'ok',
                   'suppliers': inbound_suppliers}
        return results

    @http.route('/inbound_screen/get_products', type='json', auth="user")
    def get_products(self, supplier_id, search="", page=0,  **kw):
        cr = http.request.cr
        products = list()

        if not search:
            raise exceptions.ValidationError('You have to specify at least one character')

        search_limit = 30
        search_offset = page * search_limit
        search = '%%%s%%' % search

        cr.execute("""
SELECT pp.id, pt.name, psi.name
FROM product_template AS pt
  JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
  JOIN product_supplierinfo AS psi ON pt.id = psi.product_tmpl_id,
res_partner AS rp
WHERE pt.name ilike %s
AND pt.sale_ok IS TRUE
AND psi.name = rp.id
AND rp.commercial_partner_id = %s
ORDER BY pp.id
LIMIT %s
OFFSET %s
""", [search, supplier_id, search_limit, search_offset])
        products_results = cr.fetchall()

        cr.execute("""
SELECT count(*)
FROM product_template AS pt
  JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
  JOIN product_supplierinfo AS psi ON pt.id = psi.product_tmpl_id,
res_partner AS rp
WHERE pt.name ilike %s
AND pt.sale_ok IS TRUE
AND psi.name = rp.id
AND rp.commercial_partner_id = %s
""", [search, supplier_id])

        products_count = cr.fetchall()

        for product in products_results:
            products.append({
                'id': product[0],
                'name': product[1],
                'image': "/web/binary/image?model=product.product&id=%s&field=image" % product[0]
            })

        results = {'status': 'ok',
                   'search_limit': search_limit,
                   'products': products,
                   'products_count': products_count[0][0]}
        return results

    @http.route('/inbound_screen/get_product', type='json', auth="user")
    def get_product(self, id, supplier_id, **kw):
        env = http.request.env

        if not id or not supplier_id:
            print 'Problem'

        product = env['product.product'].browse(int(id))

        supplier_info = product.seller_ids.filtered(
            lambda r: r.name.id == int(supplier_id))

        results = {
            'status': 'ok',
            'product': {
                'name': product.name,
                'description': product.description,
                'default_code': product.default_code,
                'supplier_code': supplier_info and supplier_info.product_code or 'N/A',
                'barcodes': supplier_info and supplier_info.xx_tags_ids or [],
            }
        }
        return results

    @http.route('/inbound_screen/get_carts', type='json', auth="user")
    def get_carts(self, search="",  **kw):
        env = http.request.env
        inbound_carts = list()

        domain = [('location_id', '=', env.ref('__ow__.stock_location_input').id)]

        carts = env['stock.location'].search(
            domain
        )

        for cart in carts:
            print cart.name
            inbound_carts.append({
                'id': cart.id,
                'name': cart.name,
            })

        results = {'status': 'ok',
                   'carts': inbound_carts}

        return results

    @http.route('/inbound_screen/get_cart_boxes', type='json', auth="user")
    def get_cart_boxes(self, cart_id,  **kw):
        env = http.request.env
        cart_boxes = list()
        if not cart_id:
            raise exceptions.ValidationError('You have to choose a cart')

        domain = [('location_id', '=', int(cart_id))]
        boxes = env['stock.location'].search(
            domain,
            order='name'
        )

        for box in boxes:
            cart_boxes.append({
                'id': box.id,
                'name': box.name,
            })

        print cart_boxes

        results = {'status': 'ok',
                   'cart_boxes': cart_boxes}

        return results
