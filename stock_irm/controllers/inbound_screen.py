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
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'worklocation_id': current_user.work_location_id.id or 0,
            'title': 'Inbound',
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
SELECT pp.id, pt.name
FROM product_template AS pt
  JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
  JOIN product_supplierinfo AS psi ON pt.id = psi.product_tmpl_id
  LEFT JOIN xx_product_supplierinfo_tags AS psitags on psitags.res_id = psi.id,
  res_partner AS rp

WHERE (pt.name ilike %s
OR pp.ean13 ilike %s
OR psitags.name ilike %s
OR psi.product_code ilike %s)

AND pt.sale_ok IS TRUE
AND psi.name = rp.id
AND rp.commercial_partner_id = %s
GROUP BY pt.name, pp.id
ORDER BY pp.id
LIMIT %s
OFFSET %s
""", [search, search, search, search, supplier_id, search_limit, search_offset])
        products_results = cr.fetchall()

        cr.execute("""
SELECT count(*)
FROM product_template AS pt
  JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
  JOIN product_supplierinfo AS psi ON pt.id = psi.product_tmpl_id
  LEFT JOIN xx_product_supplierinfo_tags AS psitags on psitags.res_id = psi.id,
  res_partner AS rp

WHERE (pt.name ilike %s
OR pp.ean13 ilike %s
OR psitags.name ilike %s
OR psi.product_code ilike %s)

AND pt.sale_ok IS TRUE
AND psi.name = rp.id
AND rp.commercial_partner_id = %s
""", [search, search, search, search, supplier_id])

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
                'image': "/web/binary/image?model=product.product&id=%s&field=image" % product.id,
            }
        }
        return results

    @http.route('/inbound_screen/get_carts', type='json', auth="user")
    def get_carts(self, search="",  **kw):
        env = http.request.env
        inbound_carts = list()

        domain = [('is_inbound_cart', '=', True)]

        carts = env['stock.location'].search(
            domain
        )

        for cart in carts:
            inbound_carts.append({
                'is_in_usage': cart.is_in_usage,
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

    def treat_box(self, product, cart, box_id, quantity, supplier, picking):
        env = http.request.env

        # search or create an available box on this cart
        dest_box = env['stock.location'].search([
            ('location_id', '=', cart.id),
            ('name', '=', str(box_id))
        ])

        if len(dest_box) > 1:
            message = 'Multiple locations have been found on cart "%s" with ' \
                      'the name: "%s" <br/> (product "%s") ' \
                      % (cart.name, str(box_id), product.name)

            env.cr.rollback()
            return {
                'status': 'error',
                'message': message
            }

        if not dest_box:
            dest_box = env['stock.location'].create({
                'location_id': cart.id,
                'name': str(box_id),
            })

        if not quantity:
            message = 'No quantity provided for "%s" in cart "%s"' \
                      % (product.name, cart.name)

            env.cr.rollback()
            return {
                'status': 'error',
                'message': message
            }

        quantity = self.look_for_existing_moves(supplier, product, quantity,
                                                dest_box)

        if quantity:
            picking = self.create_moves_for_leftover(picking, supplier, product,
                                                     quantity, dest_box)

        return picking

    def create_moves_for_leftover(self, picking, supplier, product, qty,
                                  dest_box):
        """
        If no stock move are found, we have to create a
        picking and a stock move
        :param picking:
        :param supplier:
        :return:
        """
        env = http.request.env

        picking_type_id = env['stock.picking.type'].search([
            ('is_receipts', '=', True)
        ])
        if not picking_type_id:
            raise Exception('Please, set a picking type to be used for'
                            'receipt')

        if not picking:
            picking = env['stock.picking'].create({
                'partner_id': supplier.id,
                'picking_type_id': picking_type_id.id,
            })

        picking.write({
            'move_lines': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': qty,
                'picking_type_id': picking_type_id.id,
                'location_dest_id': dest_box.id,
                'location_id': env.ref('stock.stock_location_suppliers').id,
                'product_uom': product.uom_id.id,
                'name': 'automated picking - %s' % product.name,
            })]
        })

        return picking

    def look_for_existing_moves(self, supplier, product, qty, dest_box):
        """
        Loop to retrieve existing receiving moves corresponding to the product
        :return:
        """
        env = http.request.env

        while qty > 0:

            # retrieve a stock move for this product
            stock_move = env['stock.move'].search([
                ('picking_id.partner_id.id', '=', supplier.id),
                ('state', '=', 'assigned'),
                ('product_id', '=', product.id),
            ], order='create_date asc', limit=1)

            if not stock_move:
                break

            qty_to_process = qty

            # The next move have to change its source location to become
            # available

            # search the quantity to process on this stock move
            if qty >= stock_move.product_uom_qty:
                qty_to_process = stock_move.product_uom_qty
                stock_move.location_dest_id = dest_box.id

                stock_move.action_done()
            else:
                stock_move.product_uom_qty -= qty_to_process

                new_move = env['stock.move'].create({
                    'product_id': stock_move.product_id.id,
                    'product_uom_qty': qty_to_process,
                    'picking_type_id': stock_move.picking_type_id.id,
                    'location_dest_id': dest_box.id,
                    'location_id': stock_move.location_id.id,
                    'product_uom': stock_move.product_uom.id,
                    'name': stock_move.name,
                    'picking_id': stock_move.picking_id.id,
                })
                new_move.action_done()


            qty -= qty_to_process

            # create the pack operation
            # pack_datas = {
            #     'product_id': product.id,
            #     'product_uom_id': product.uom_id.id,
            #     'product_qty': qty_to_process,
            #     'location_id': env.ref('stock.stock_location_suppliers').id,
            #     'location_dest_id': dest_box.id,
            #     'date': datetime.now(),
            #     'picking_id': stock_move.picking_id.id,
            # }

            # env['stock.pack.operation'].create(pack_datas)


        return qty

    def create_pack_operation(self, picking):
        env = http.request.env

        for line in picking.move_lines:
            pack_datas = {
                'product_id': line.product_id.id,
                'product_uom_id': line.product_id.uom_id.id,
                'product_qty': line.product_uom_qty,
                'location_id': line.location_id.id,
                'location_dest_id': line.location_dest_id.id,
                'date': datetime.now(),
                'picking_id': picking.id,
            }

            env['stock.pack.operation'].create(pack_datas)

    @http.route('/inbound_screen/process_picking', type='json', auth="user")
    def process_picking(self, supplier_id, results,  **kw):
        env = http.request.env
        supplier = env['res.partner'].browse(supplier_id)
        picking = False

        # pickings is a list of products, within which there is a list of carts
        # and a quantity by carts
        try:
            for product_id, cart_dict in results.iteritems():
                product = env['product.product'].browse(int(product_id))

                # multiple location could be found for the same product
                for cart_id, location_dict in cart_dict.iteritems():
                    if location_dict.get('index'):
                        del(location_dict['index'])

                    cart = env['stock.location'].browse(int(cart_id))

                    for box_id, quantity in location_dict.iteritems():
                        picking = self.treat_box(product, cart, box_id,
                                                 quantity, supplier, picking)

            if picking:
                picking.action_confirm()
                self.create_pack_operation(picking)
                picking.do_transfer()


            results = {
                'status': 'ok',
                'nb_picking_created': 0,
                'nb_picking_filled': 0,
            }
            return results

        except Exception as e:
            raise
            return {'status': 'error',
                    'error' : type(e).__name__,
                    'message': str(e)}

    @http.route('/inbound_screen/change_user', type='http', auth="user")
    def change_user(self, **kw):
        request.session.logout(keep_db=True)
        request.session.authenticate(request.session.db, login=kw['login'],
                                     password=kw['password'])

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

    @http.route('/inbound_screen/switch_worklocation',
                type='json',
                auth="user")
    def switch_worklocation(self, new_work_location_id, **kw):
        env = http.request.env
        user = env['res.users'].browse(request.uid)
        user.work_location_id = int(new_work_location_id)

        return self.get_printer_ip()

    @http.route('/inbound_screen/get_printer_ip', type='json', auth="user")
    def get_printer_ip(self, **kw):
        env = http.request.env
        WorkLocationPrinter = env['work_location_printer']
        label_printer_type = env.ref('stock_irm.label_printer_type')
        printer_ip = False

        user = env['res.users'].browse(request.uid)

        work_location_printer = WorkLocationPrinter.search(
            [('document_type_id', '=', label_printer_type.id),
             ('work_location_id', '=', user.work_location_id.id)])

        if work_location_printer.printing_printer_id:
            printer_ip = work_location_printer.printing_printer_id.ip_adress

        results = {'status': 'ok',
                   'printer_ip': printer_ip}
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

    @http.route('/inbound_screen/book_cart',
                type='json',
                auth="user")
    def book_cart(self, cart_id, **kw):
        env = http.request.env

        env['stock.location'].browse(int(cart_id)).is_in_usage = True
