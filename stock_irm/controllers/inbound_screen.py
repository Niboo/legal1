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
            'work_location_staging_id': current_user.work_location_id.staging_location_id.id,
            'title': 'Inbound',
            'user_email': current_user.partner_id.email,
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
  LEFT JOIN xx_product_supplierinfo_tags AS psitags on psitags.res_id = psi.id

WHERE (pt.name ilike %s
OR pp.ean13 ilike %s
OR pp.default_code ilike %s
OR psitags.name ilike %s
OR psi.product_code ilike %s)

AND pt.sale_ok IS TRUE
AND psi.name = %s
GROUP BY pt.name, pp.id
ORDER BY pp.id
LIMIT %s
OFFSET %s
""", [search, search, search, search, search, supplier_id, search_limit, search_offset])
        products_results = cr.fetchall()

        cr.execute("""
SELECT count(*)
FROM product_template AS pt
  JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
  JOIN product_supplierinfo AS psi ON pt.id = psi.product_tmpl_id
  LEFT JOIN xx_product_supplierinfo_tags AS psitags on psitags.res_id = psi.id

WHERE (pt.name ilike %s
OR pp.ean13 ilike %s
OR pp.default_code ilike %s
OR psitags.name ilike %s
OR psi.product_code ilike %s)

AND pt.sale_ok IS TRUE
AND psi.name = %s
""", [search, search, search, search, search, supplier_id])

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

        supplier = env['res.partner'].browse(int(supplier_id))

        # retrieve the partner and its child to search for supplier info
        supplier_childs = supplier.child_ids

        supplier_info = product.seller_ids.filtered(
            lambda r: r.name.id == supplier.id)

        if len(supplier_info) != 1:
            results = {
                'status': 'error',
                'message': """
There is more or less than one supplier info for this product:
product id: %s, supplier id: %s
""" % (product.id, supplier_id)
            }
            return results

        requires_unpack = supplier_info.requires_unpack
        requires_relabel = supplier_info.requires_relabel

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
                'requires_unpack': requires_unpack,
                'requires_relabel': requires_relabel,
                'barcodes': barcodes,
                'barcode_to_print': product.default_code or product.ean13,
                'image': "/web/binary/image?model=product.product&id=%s&field=image" % product.id,
            }
        }
        return results

    @http.route('/inbound_screen/check_package_empty', type='json',
                auth='user')
    def check_package_empty(self, package_barcode):
        env = http.request.env

        dest_package = env['stock.quant.package'].search([
            ('barcode', '=', str(package_barcode))
        ])

        if dest_package and (dest_package.quant_ids or
                                 dest_package.children_ids):
            return {'status': 'error'}

        return {'status': 'ok'}

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

    @http.route('/inbound_screen/search_supplier_purchase', type='json',
                auth='user')
    def search_supplier_purchase(self, supplier):
        env = http.request.env
        supplier = env['res.partner'].search([('id', '=', int(supplier))])

        purchase_orders = env['purchase.order'].search([
            ('partner_id', '=', supplier.id),
            ('state', '=', 'approved'),
            ('shipped', '=', False),
        ], order="date_order ASC")

        orders = []
        for order in purchase_orders:
            orders.append({'name': order.name,
                           'id': order.id})

        return {'status': 'ok',
                'orders': orders}

    @http.route('/inbound_screen/get_purchase_order_move_lines', type='json',
                auth='user')
    def get_purchase_order_move_lines(self, purchase_order_ids=False):
        env = http.request.env
        purchase_orders = env['purchase.order'].browse(purchase_order_ids)



        pickings = purchase_orders.mapped('picking_ids').filtered(
            lambda r: r.state == 'assigned')
        pickings = pickings.sorted(key=lambda pick: (pick.min_date, pick.id))

        lines = []
        for picking in pickings:
            lines.extend(self.prepare_picking_lines(picking))

        return {'status': 'ok',
                'po_move_lines': lines}

    def prepare_picking_lines(self, picking):
        lines = []
        for move_line in picking.move_lines.filtered(
                lambda r: r.state == 'assigned'):

            lines.append({
                'product_id': move_line.product_id.id,
                'quantity': move_line.product_qty,
                'id': move_line.id,
                'picking_name': picking.name,
                'picking_id': picking.id,
                'product_name': move_line.product_id.name[0:20],
                'progress_done': 0,
                'quantity_already_scanned': 0,
                'is_new': False,
            })
        return lines

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
                'work_location_staging_id': location.staging_location_id.id,
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
        proxy_address = False

        user = env['res.users'].browse(request.uid)

        work_location_printer = WorkLocationPrinter.search(
            [('document_type_id', '=', label_printer_type.id),
             ('work_location_id', '=', user.work_location_id.id)])

        if work_location_printer.printing_printer_id:
            printer = work_location_printer.printing_printer_id
            printer_ip = printer.ip_adress
            if printer.xx_proxy_id:
                proxy_address = printer.xx_proxy_id.proxy_address

        return {
            'status': 'ok',
            'printer_ip': printer_ip,
            'proxy': proxy_address,
        }

    @http.route('/inbound_screen/get_worklocation_printers',
                type='json',
                auth="user")
    def get_worklocation_printers(self, location_id, **kw):
        env = http.request.env
        wklc = env['work_location']

        printers = []
        for line in wklc.browse(int(location_id)).work_location_printer_ids:
            printer = line.printing_printer_id
            printers.append({
                'id': printer.id,
                'ip_adress': printer.ip_adress,
                'proxy': printer.xx_proxy_id.proxy_address or False,
            })
        return {'status': 'ok',
                'printers': printers}

    @http.route('/inbound_screen/get_user', type='json', auth="user")
    def get_user(self, barcode="",  **kw):
        env = http.request.env
        domain = []

        if barcode:
            domain.append(('login_barcode', '=', barcode))

        user = env['res.users'].search(
            domain
        )

        if user:
            user_image = "/web/binary/image?model=res.users&" \
                         "id=%s&field=image_medium" % user.id
            return {'status': 'ok',
                    'username': user.name,
                    'user_id': user.id,
                    'login': user.login,
                    'image': user_image}
        else:
            return {"status": 'error'}

    @http.route('/inbound_screen/process_picking_line', type='json',
                auth="user")
    def process_picking_line(self, qty, picking_line_id, box_name,
                             packing_order_id, reason_id=False, cart_id=False):
        env = http.request.env
        picking_line = env['stock.move'].browse(int(picking_line_id))

        destination, bo = self.process_transfer(qty, picking_line, box_name)

        env.cr.commit()

        picking_line.write({'packing_order_id': packing_order_id,
                            'reason_id': reason_id})

        dest_list = self.get_destinations(destination)

        if filter(lambda dest: dest['id'] == cart_id, dest_list):
            destination_id = cart_id
        else:
            destination_id = dest_list[0]['id']

        destination = self.move_to_destination(box_name, destination_id)

        lines = self.prepare_picking_lines(bo)
        return {'status': 'ok',
                'destination': destination['destination'],
                'po_move_lines': lines,
                'from_picking_id': bo.backorder_id.id}

    def process_transfer(self, qty, picking_line, box_name):
        env = http.request.env
        picking = picking_line.picking_id

        result = picking.do_enter_transfer_details()
        wizard_id = result['res_id']
        my_wizard = env['stock.transfer_details'].browse(wizard_id)

        dest_package = self.search_dest_package(box_name)

        line = {
            'result_package_id': dest_package.id,
            'quantity': qty,
            'product_id': picking_line.product_id.id,
            'destinationloc_id': picking_line.location_dest_id.id,
            'sourceloc_id': picking_line.location_id.id,
            'product_uom_id': picking_line.product_id.uom_id.id,
        }

        my_wizard.write({
            'item_ids': [(5,0,0),(0, False, line)]
        })

        my_wizard.sudo().do_detailed_transfer()

        bo = env['stock.picking'].search([('backorder_id','=',picking.id)])

        return picking_line.move_dest_id.location_dest_id, bo

    def transfer_to_next_location(self, package, destination_id=False):
        env = http.request.env

        quant = package.quant_ids[0]
        picking = quant.reservation_id.picking_id

        self.check_destination(picking, destination_id)

        wizard_id = picking.do_enter_transfer_details()['res_id']
        wizard = env['stock.transfer_details'].browse(wizard_id)

        line = {
            'package_id': package.id,
            'sourceloc_id': package.location_id.id,
            'destinationloc_id': int(destination_id),
        }

        wizard.write({
            'item_ids': [(5,0,0)],
            'packop_ids': [(5,0,0),(0, False, line)]
        })

        wizard.sudo().do_detailed_transfer()

    def check_destination(self, picking, destination_id):
        dest_location = picking.picking_type_id.default_location_dest_id
        dest_locations_list = [dest_location.id]
        dest_locations_list.extend(dest_location._get_sublocations())

        if destination_id not in dest_locations_list:
            raise exceptions.Warning('The location selected is not a correct '
                                     'location for this move.')

    def move_to_destination(self, box_name, destination_id, **kw):
        env = http.request.env
        package = self.search_dest_package(box_name)
        self.transfer_to_next_location(package, destination_id)

        destination = env['stock.location'].browse(int(destination_id))
        return {'status': 'ok',
                'destination': destination.name}

    @http.route('/inbound_screen/get_incomplete_reason',
                type='json',
                auth="user")
    def get_incomplete_reason(self):
        env = http.request.env

        reasons = env['stock.incomplete.reason'].search([])
        reason_list = []
        for reason in reasons:
            reason_list.append({'name': reason.name,
                                'id': reason.id})

        return {'status': 'ok',
                'reasons': reason_list}

    @http.route('/inbound_screen/check_staging_package_empty',
                type='json',
                auth="user")
    def check_staging_package_empty(self, barcode):
        env = http.request.env

        staging_location = env.ref('stock_irm.stock_staging_location')

        dest_box = env['stock.location'].search([
            ('location_id', '=', staging_location.id),
            ('name', '=', str(barcode))
        ])

        if len(dest_box) > 1:
            message = 'There is already a box with that barcode on the staging location'

            env.cr.rollback()
            return {
                'status': 'error',
                'message': message
            }

        if not dest_box:
            dest_box = env['stock.location'].sudo().create({
                'location_id': staging_location.id,
                'name': str(barcode),
            })

        return {
            'status': "ok",
            'dest_box_id': dest_box.id
        }

    # This method is used for both unordered product and product that were
    # ordered but came in with too many items
    @http.route('/inbound_screen/create_picking_for_unordered_lines',
                type='json',
                auth="user")
    def create_picking_for_unordered_lines(
            self, extra_line, dest_box_id, supplier_id, box_name,
            packing_order_id, reason_id=False, cart_id=False):
        env = http.request.env

        picking, move_line = self.create_picking(
            supplier_id, extra_line['product_id'],
            extra_line['quantity_already_scanned'],
        )
        env.cr.commit()

        result = picking.do_enter_transfer_details()
        wizard_id = result['res_id']
        my_wizard = env['stock.transfer_details'].browse(wizard_id)

        dest_package = self.search_dest_package(box_name)

        for wizard_line in my_wizard.item_ids:
            wizard_line.result_package_id = dest_package.id
            wizard_line.destinationloc_id = int(dest_box_id)

        my_wizard.sudo().do_detailed_transfer()
        env.cr.commit()

        dest_list = self.get_destinations(
            move_line.move_dest_id.location_dest_id)

        self.add_packing_order_on_move(picking, packing_order_id, reason_id)

        if filter(lambda dest: dest['id'] == cart_id, dest_list):
            destination_id = cart_id
        else:
            destination_id = dest_list[0]['id']

        destination = self.move_to_destination(box_name, destination_id)

        return {'status': 'ok',
                'destination': destination['destination']}

    def create_picking(self, supplier_id, product_id, quantity):
        env = http.request.env

        picking_type_id = self.get_receipt_picking_type()

        picking = env['stock.picking'].create({
            'partner_id': int(supplier_id),
            'picking_type_id': picking_type_id.id,
        })

        product = env['product.product'].browse(int(product_id))
        move_line = env['stock.move'].create({
            'product_id': product.id,
            'product_uom_qty': quantity,
            'picking_type_id': picking_type_id.id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'location_id': env.ref('stock.stock_location_suppliers').id,
            'product_uom': product.uom_id.id,
            'name': 'automated picking - %s' % product.name,
            'picking_id': picking.id,
        })
        picking.action_confirm()

        return picking, move_line


    def get_destinations(self, location):
        locations = location.search([
            ('location_id', '=', location.id), ('is_inbound_cart', '=', True)
        ])

        locations_list = []
        if locations:
            for location in locations:
                locations_list.append({
                    'name': location.name,
                    'id': location.id,
                })
        else:
            if location:
                locations_list.append({
                    'name': location.name,
                    'id': location.id,
                })

        return locations_list

    def add_packing_order_on_move(self, picking, packing_order_id, reason_id = False):
        for move in picking.move_lines:
            move.write({'packing_order_id': packing_order_id,
                        'reason_id': reason_id})

    @http.route('/inbound_screen/create_packing_order', type='json', auth="user")
    def create_packing_order(self, **kw):
        env = http.request.env
        packing_order = env['stock.packing.order'].create({})
        return {'status': 'ok',
                'packing_reference':packing_order.name,
                'packing_id': packing_order.id,
                }

    @http.route('/inbound_screen/save_packing_note', type='json', auth='user')
    def save_packing_note(self, packing_id, note, **kw):
        env = http.request.env
        packing_oder = env['stock.packing.order'].browse(int(packing_id))
        packing_oder.note = note
        return {'status': 'ok'}

    @http.route('/inbound_screen/get_cart_list', type='json', auth='user')
    def get_cart_list(self):
        env = http.request.env
        locations = env['stock.location']\
            .search([('is_inbound_cart', '=', True)])

        carts = []
        for location in locations:
            carts.append({
                'id': location.id,
                'name': location.name,
                'is_in_usage': location.is_in_usage,
            })
        return {
            'status': 'ok',
            'carts': carts,
        }

    @http.route('/inbound_screen/get_damage_reasons', type='json', auth="user")
    def get_damage_reasons(self):
        env = http.request.env
        damage_reasons_objects = env['stock.inbound.damage.reason'].search([])
        damage_reasons = [str(damage_reason.reason)
                          for damage_reason in damage_reasons_objects]
        if damage_reasons:
            return {
                'status': 'ok',
                'damage_reasons': damage_reasons
            }
        else:
            return {
                'status': 'error',
                'error': 'Error',
                'message': 'There are currently no Damage Reasons set.'
            }

    @http.route('/inbound_screen/move_to_damaged', type='json', auth="user")
    def move_to_damaged(self, product_id, qty, reason, move_id, supplier_id):
        env = http.request.env
        product_id = int(product_id)
        move = env['stock.move'].browse(int(move_id))
        product = env['product.product'].browse(product_id)

        if not move_id:
            picking, move = self.create_picking(supplier_id,
                                                product_id, qty)

        scrap_obj = env['stock.move.scrap']
        move_scrap = scrap_obj.with_context(active_id=move.id).create({
            'product_id': product.id,
            'product_qty': int(qty),
            'product_uom': product.uom_id.id,
        })

        move_scrap.with_context(active_ids=[move.id]).move_scrap()

        return {
            'status': 'ok',
            'scrap_line': {
                'name': move_scrap.product_id.name,
                'qty': qty,
                'reason': reason,
            }
        }
