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
from datetime import datetime
from openerp.http import request


class InboundController(http.Controller):
    @http.route('/inbound_screen', type='http', auth="user")
    def inbound_screen(self, **kw):
        current_user = http.request.env['res.users'].browse(http.request.uid)
        inbound_suppliers = http.request.env['res.partner'].search([
            ('is_in_inbound', '=', True)],
            order='sequence'
        )

        return http.request.render('stock_irm.inbound_screen', {
            'suppliers': inbound_suppliers,
            'user_name': current_user.partner_id.name
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
  JOIN product_supplierinfo AS psi ON pt.id = psi.product_tmpl_id
  JOIN xx_product_supplierinfo_tags AS psitags on psitags.res_id = psi.id,
  res_partner AS rp

WHERE (pt.name ilike %s
OR pp.ean13 ilike %s
OR psitags.name ilike %s)

AND pt.sale_ok IS TRUE
AND psi.name = rp.id
AND rp.commercial_partner_id = %s
ORDER BY pp.id
LIMIT %s
OFFSET %s
""", [search, search, search, supplier_id, search_limit, search_offset])
        products_results = cr.fetchall()

        cr.execute("""
SELECT count(*)
FROM product_template AS pt
  JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
  JOIN product_supplierinfo AS psi ON pt.id = psi.product_tmpl_id
  JOIN xx_product_supplierinfo_tags AS psitags on psitags.res_id = psi.id,
  res_partner AS rp

WHERE (pt.name ilike %s
OR pp.ean13 ilike %s
OR psitags.name ilike %s)

AND pt.sale_ok IS TRUE
AND psi.name = rp.id
AND rp.commercial_partner_id = %s
""", [search, search, search, supplier_id])

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

        # retrieve the partner and its child to search for supplier info
        supplier_childs = env['res.partner'].browse(int(supplier_id)).child_ids

        supplier_info = product.seller_ids.filtered(
            lambda r: r.name.id == int(supplier_id) or
                      r.name.id in supplier_childs.ids)

        if len(supplier_info) != 1:
            results = {
                'status': 'error',
                'message': """
There is more or less than one supplier info for this product:
product id: %s, supplier id: %s
""" % (product.id, supplier_id)
            }
            return results
        barcodes = supplier_info.xx_tag_ids.mapped('name')
        if product.ean13:
            barcodes.append(product.ean13)

        results = {
            'status': 'ok',
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'default_code': product.default_code,
                'supplier_code': supplier_info.product_code or 'N/A',
                'barcodes': barcodes,
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

        results = {'status': 'ok',
                   'cart_boxes': cart_boxes}

        return results

    @http.route('/inbound_screen/process_picking', type='json', auth="user")
    def process_picking(self, supplier_id, pickings,  **kw):
        env = http.request.env
        supplier = env['res.partner'].browse(supplier_id)
        nb_picking_created = 0
        nb_picking_filled = 0
        stock_move_lines = []
        stock_picking = False

        # pickings is a list of products, within which there is a list of carts
        # and a quantity by carts
        for product_id, cart_dict in pickings.iteritems():
            product = env['product.product'].browse(int(product_id))

            # multiple location could be found for the same product
            for cart_id, location_dict in cart_dict.iteritems():
                del(location_dict['index'])

                cart = env['stock.location'].browse(int(cart_id))

                for box_id, quantity in location_dict.iteritems():
                    qty = quantity

                    # search or create an available box on this cart
                    dest_box = env['stock.location'].search([
                        ('location_id', '=', int(cart_id)),
                        ('name', '=', str(box_id))
                    ])

                    if len(dest_box) > 1:

                        message = """
Multiple locations have been found on cart "%s" with the name: "%s" <br/>
(product "%s") """ % (cart.name, str(box_id), product.name)

                        env.cr.rollback()
                        results = {'status': 'error',
                                   'message': message
                                   }
                        return results

                    if not dest_box:
                        dest_box = env['stock.location'].create({
                            'location_id': int(cart_id),
                            'name': str(box_id),
                        })

                    if not qty:
                        message = """
No quantity provided for "%s" in cart "%s" """ % (product.name, cart.name)

                        env.cr.rollback()
                        results = {'status': 'error',
                                   'message': message
                                   }
                        return results

                    while qty > 0:
                        # retrieve a stock move for this product
                        stock_move = env['stock.move'].search([
                            ('picking_id.partner_id', '=', supplier.id),
                            ('picking_id.state', '=', 'assigned'),
                            ('product_id', '=', product.id),
                        ], order='create_date asc', limit=1)

                        if not stock_move:
                            if not stock_picking:
                                stock_picking = env['stock.picking'].create({
                                    'partner_id': supplier.id,
                                    # 'move_lines': stock_move_lines,
                                    'picking_type_id':
                                        env.ref('__ow__.stock_picking_type_receipts').id,
                                })
                            # if no stock move are found, we have to create a
                            # picking and a stock move
                            stock_move_lines.append((0, 0, {
                                'product_id': product.id,
                                'product_uom_qty': qty,
                                'picking_type_id':
                                    env.ref('__ow__.stock_picking_type_receipts').id,
                                'location_dest_id':
                                    dest_box.id,
                                'location_id':
                                    env.ref('stock.stock_location_suppliers').id,
                                'product_uom': product.uom_id.id,
                                'name': 'automated picking - %s' % product.name,
                            }))

                        # search the quantity to process on this stock move
                        if stock_move.product_uom_qty and qty >= stock_move.product_uom_qty:
                            qty_to_process = stock_move.product_uom_qty
                            nb_picking_filled += 1
                        else:
                            qty_to_process = qty

                        # compute the remaining quantity to process
                        qty = qty - qty_to_process

                        # create the pack operation
                        pack_datas = {
                            'product_id': product.id,
                            'product_uom_id': product.uom_id.id,
                            'product_qty': qty_to_process,
                            'location_id': env.ref('stock.stock_location_suppliers').id,
                            'location_dest_id': dest_box.id,
                            'date': datetime.now(),
                            'picking_id': stock_picking.id,
                        }

                        env['stock.pack.operation'].create(pack_datas)
                        stock_move.picking_id.do_transfer()
        if stock_move_lines:
            stock_picking.move_lines = stock_move_lines

        results = {'status': 'ok',
                   'nb_picking_created': nb_picking_created,
                   'nb_picking_filled': nb_picking_filled,
                   }

        return results

    @http.route('/inbound_screen/change_user', type='http', auth="user")
    def change_user(self, login, login_code, **kw):
        code = int(login_code)

        if(code == -1):
            raise exceptions.ValidationError('This code is invalid')

        current_user = http.request.env['res.users'].search(
            [('login','=',login),
             ('login_code','=',login_code),
             ('active','=',True)]
        )

        if not current_user:
            raise exceptions.ValidationError('No user logged!')

        # request.session.logout(keep_db=True)
        # request.session.authenticate(request.session.db, login=current_user.login,
        #                               password=current_user.password)

        # self.db = request.session.db
        # self.uid = current_user.id
        # self.login = current_user.login
        # self.password = current_user.password
        # request.uid = current_user.id
        # request.disable_db = False


        inbound_suppliers = http.request.env['res.partner'].search([
            ('is_in_inbound', '=', True)],
            order='sequence'
        )

        return http.request.render('stock_irm.inbound_screen', {
            'suppliers': inbound_suppliers,
            'user_name': current_user.partner_id.name,
            'image': "/web/binary/image?model=res.users&id=%s&field=image_medium" % current_user.id
        })

    @http.route('/inbound_screen/get_worklocations', type='json', auth="user")
    def get_worklocation(self, **kw):
        env = http.request.env
        wklc = env['work_location']
        worklocations = list()
        domain = []

        wklc = wklc.search(domain)

        for location in wklc:
            worklocations.append({
                'id': location.id,
                'name': location.name,
            })

        results = {'status': 'ok',
                   'worklocations': worklocations}

        return results

    @http.route('/inbound_screen/get_worklocation_printers',
                type='json',
                auth="user")
    def get_worklocation_printers(self, location_id, **kw):
        env = http.request.env
        wklc = env['work_location']

        printers = []
        for line in wklc.browse(int(location_id)).work_location_printer_ids:
            printers.append({'id':line.printing_printer_id.id,
                             'ip_adress':line.printing_printer_id.ip_adress})
        results = {'status': 'ok',
                   'printers': printers}

        return results

    @http.route('/inbound_screen/get_user', type='json', auth="user")
    def get_user(self, barcode="",  **kw):
        env = http.request.env
        domain = []

        if barcode:
            domain.append(('login_barcode','=',barcode))

        user = env['res.users'].search(
            domain
        )

        if user:
            results = {'status': 'ok',
                       'username': user.name,
                       'user_id':user.id,
                       'login':user.login,
                       'image': "/web/binary/image?model=res.users&id=%s&field=image_medium" % user.id}

            return results
        else:
            return {"status": 'error'};
