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

        domain = [('is_in_inbound', '=', True)]

        if search:
            domain.append(('display_name', 'ilike', search))

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
        return {'status': 'ok',
                   'suppliers': inbound_suppliers}

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
                'description': product.description or "No description",
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

        return {'status': 'ok',
                   'carts': inbound_carts}

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

        return {'status': 'ok',
                   'cart_boxes': cart_boxes}

    def search_dest_box(self, box_name, cart, product):
        env = http.request.env

        dest_box = env['stock.location'].search([
            ('location_id', '=', int(cart.id)),
            ('name', '=', str(box_name))
        ])

        if len(dest_box) > 1:
            message = 'Multiple locations have been found on cart "%s" with ' \
                      'the name: "%s" <br/> (product "%s") ' \
                      % (cart.name, str(box_name), product.name)

            env.cr.rollback()
            return {
                'status': 'error',
                'message': message
            }

        if not dest_box:
            dest_box = env['stock.location'].sudo().create({
                'location_id': cart.id,
                'name': str(box_name),
            })

        return dest_box

    @http.route('/inbound_screen/check_package_empty', type='json',
                auth='user')
    def check_package_empty(self, package_barcode):
        env = http.request.env

        dest_package = env['stock.quant.package'].search([
            ('barcode', '=', str(package_barcode))
        ])

        if dest_package and (dest_package.quant_ids or
                                 dest_package.children_ids):
            return{
                'status': 'error'
            }

        return {
            "status": "ok"
        }


    def search_dest_package(self, package_barcode):
        env = http.request.env

        dest_package = env['stock.quant.package'].search([
            ('barcode', '=', str(package_barcode))
        ])

        if not dest_package:
            dest_package = env['stock.quant.package'].create({
                'name': str(package_barcode),
                'barcode': str(package_barcode),
            })

        return dest_package

    def no_quantity_error(self, product, cart):
        env = http.request.env

        message = 'No quantity provided for "%s" in cart "%s"' \
                      % (product.name, cart.name)

        env.cr.rollback()
        return {
            'status': 'error',
            'message': message
        }

    def create_moves_for_leftover(self, picking, supplier, product, qty,
                                  dest_box):
        """we have to create a picking and a stock move
        :param picking:
        :param supplier:
        :return:
        """
        env = http.request.env

        picking_type_id = self.get_receipt_picking_type()

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

    @http.route('/inbound_screen/search_supplier_purchase', type='json',
                auth='user')
    def search_supplier_purchase(self, supplier):
        env = http.request.env
        supplier = env['res.partner'].search([('id', '=', int(supplier))])

        purchase_orders = env['purchase.order'].search([
            ('partner_id.commercial_partner_id', '=',
             supplier.commercial_partner_id.id),
            ('state', '=', 'approved'),
            ('shipped', '=', False),
        ], order="date_order ASC")

        orders = []
        for order in purchase_orders:
            orders.append({'name': order.name,
                           'id': order.id})

        return {'status': 'ok',
                   'orders': orders}

    @http.route('/inbound_screen/process_picking', type='json', auth="user")
    def process_picking(self, supplier_id, results, purchase_orders, note,
                        packing_id,  **kw):
        env = http.request.env

        try:
            supplier = env['res.partner'].browse(int(supplier_id))
            packing_order = env['stock.packing.order'].browse(int(packing_id))
            # TODO: retrieve packing order here!

            if purchase_orders:
                picking_ids = \
                    self.retrieve_pickings_from_orders(purchase_orders)

                product_quantities = self.create_product_qty_dict(results)
                self.treat_pickings(picking_ids, product_quantities, results,
                                    packing_order)

            self.create_whole_new_picking(supplier, results, packing_order)

            return{
                'status': 'ok',
                'nb_picking_created': 0,
                'nb_picking_filled': 0,
            }

        except Exception as e:
            return {'status': 'error',
                    'error': type(e).__name__,
                    'message': e.value}

    def create_whole_new_picking(self, supplier, inbound_list, packing_order):
        env = http.request.env

        picking = False
        picking_type_id = self.get_receipt_picking_type()

        for product_id, cart_dict in inbound_list.iteritems():
            product = env['product.product'].browse(int(product_id))

            # multiple location could be found for the same product
            for cart_id, location_dict in cart_dict.iteritems():
                if location_dict.get('index'):
                    del(location_dict['index'])

                cart = env['stock.location'].browse(int(cart_id))

                for box_id, quantity in location_dict.iteritems():
                    if box_id != "package_barcode":
                        if not quantity:
                            self.no_quantity_error(product, cart)

                        if not picking:
                            picking = env['stock.picking'].create({
                                'partner_id': supplier.id,
                                'picking_type_id': picking_type_id.id,
                            })

                        input_location = env.ref('stock.stock_location_company')
                        self.create_moves_for_leftover(picking, supplier, product,
                                                         quantity, input_location)

        if not picking:
            return

        product_quantities = self.create_product_qty_dict(inbound_list)

        picking.action_confirm()
        self.treat_pickings(picking, product_quantities, inbound_list, packing_order)

        return {
            'status': 'ok',
            'nb_picking_created': 0,
            'nb_picking_filled': 0,
        }

    def get_receipt_picking_type(self):
        env = http.request.env

        picking_type_id = env['stock.picking.type'].search([
            ('is_receipts', '=', True)
        ])

        if not picking_type_id:
            raise exceptions.ValidationError(
                'Please, set a picking type to be used for receipt')


        return picking_type_id

    def retrieve_pickings_from_orders(self, purchase_orders):
        env = http.request.env
        picking_ids = []

        # retrieve the pickings related to the selected orders
        purchases = env['purchase.order'].search([
            ('id', 'in', purchase_orders)
        ], order='id ASC')

        for purchase in purchases:
            # retrieve only the picking that are not done yet
            for picking in purchase.picking_ids.filtered(
                    lambda r: r.state != 'done'):

                if picking.state != 'done':
                    picking_ids.append(picking)

        return picking_ids

    def create_product_qty_dict(self, results):
        product_quantities = dict()
        env = http.request.env

        for product_id, cart_dict in results.iteritems():
            product = env['product.product'].browse(int(product_id))

            # multiple location could be found for the same product
            for cart_id, location_dict in cart_dict.iteritems():
                if location_dict.get('index'):
                    del(location_dict['index'])

                cart = env['stock.location'].browse(int(cart_id))
                for box_id, quantity in location_dict.iteritems():
                    if box_id != "package_barcode":
                        if not quantity:
                            self.no_quantity_error(product, cart)
                        if product.id in product_quantities.keys():
                            product_quantities[product.id] += quantity
                        else:
                            product_quantities[product.id] = quantity

        return product_quantities

    def treat_pickings(self, picking_ids, product_quantity_dict, results, packing_order):
        env = http.request.env

        for picking in picking_ids:

            result = picking.do_enter_transfer_details()
            wizard_id = result['res_id']
            my_wizard = env['stock.transfer_details'].browse(wizard_id)

            do_validate_picking = False

            for wizard_line in my_wizard.item_ids:
                product = wizard_line.product_id
                line_quantity = wizard_line.quantity
                available_quantity = product_quantity_dict.get(product.id, 0)

                if available_quantity > 0:
                    do_validate_picking = True
                    product_quantity_dict[product.id] -= line_quantity
                    self.treat_picking_line(wizard_line, product, results)

                else:
                    wizard_line.quantity = 0
                    continue

            if do_validate_picking:
                my_wizard.do_detailed_transfer()
                for line in picking.move_lines:
                    line.packing_order_id = packing_order.id

    def treat_picking_line(self, wizard_line_to_treat, product, results):
        env = http.request.env
        cart_dict = results[str(product.id)]

        for cart_id, location_dict in cart_dict.iteritems():
            cart = env['stock.location'].browse(cart_id)
            item_to_delete = []

            for box_id, box_quantity in location_dict.iteritems():
                if not wizard_line_to_treat:
                    break
                wizard_line = wizard_line_to_treat

                dest_box = self.search_dest_box(box_id, cart, product)

                # Treat results dict
                if box_id != "package_barcode":
                    location_dict[box_id] -= wizard_line.quantity
                    if location_dict[box_id] <= 0:
                        item_to_delete.append(box_id)

                    # Treat wizard
                    wizard_line.destinationloc_id = dest_box.id
                    wizard_line_to_treat = False

                    dest_package = self.search_dest_package(
                        cart_dict[cart_id]['package_barcode']
                    )
                    wizard_line.result_package_id = dest_package.id

                    if box_quantity < wizard_line.quantity:
                        wizard_line_dict = {
                            'product_id': product.id,
                            'quantity': wizard_line.quantity - box_quantity,
                            'sourceloc_id': wizard_line.sourceloc_id.id,
                            'destinationloc_id': wizard_line.destinationloc_id.id,
                            'transfer_id': wizard_line.transfer_id.id,
                            'product_uom_id': wizard_line.product_uom_id.id,
                            'result_package_id': dest_package.id
                        }

                        wizard_line.quantity = box_quantity
                        wizard_line_to_treat = wizard_line.create(wizard_line_dict)

            for item in item_to_delete:
                del(location_dict[item])

        if wizard_line_to_treat:
            wizard_line_to_treat.unlink()

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

        return {'status': 'ok',
               'worklocations': worklocations}


    @http.route('/inbound_screen/switch_worklocation',
                type='json',
                auth="user")
    def switch_worklocation(self, new_work_location_id, **kw):
        env = http.request.env
        user = env['res.users'].browse(request.uid)
        user.sudo().work_location_id = int(new_work_location_id)

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

        return{'status': 'ok',
                   'printer_ip': printer_ip}

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
        return {'status': 'ok',
                   'printers': printers}

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
            return {'status': 'ok',
                       'username': user.name,
                       'user_id':user.id,
                       'login':user.login,
                       'image': "/web/binary/image?model=res.users&id=%s&field=image_medium" % user.id}
        else:
            return {"status": 'error'};

    @http.route('/inbound_screen/book_cart',
                type='json',
                auth="user")
    def book_cart(self, cart_id, **kw):
        env = http.request.env

        env['stock.location'].browse(int(cart_id)).sudo().is_in_usage = True

    @http.route('/inbound_screen/create_packing_order', type='json', auth="user")
    def create_packing_order(self, **kw):
        env = http.request.env
        packing_order = env['stock.packing.order'].create({})
        return {"status": 'ok',
                'packing_reference':packing_order.name,
                'packing_id': packing_order.id
                };
