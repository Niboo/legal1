# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Pierre Faniel
#    Copyright 2016 Niboo SPRL
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


class RMAScreenController(http.Controller):
    @http.route('/rma_screen', type='http', auth='user')
    def rma_screen(self, **kw):
        env = http.request.env
        work_location = env.user.work_location_id
        return http.request.render('stock_irm.rma_screen', {
            'user_name': env.user.partner_id.name,
            'worklocation_name': work_location.name,
            'worklocation_id': work_location.id or 0,
            'work_location_staging_id': work_location.staging_location_id.id,
            'title': 'RMA',
        })

    @http.route('/rma_screen/get_customers', type='json', auth='user')
    def get_suppliers(self, search='',  **kw):
        env = http.request.env
        stages = env['crm.claim.stage'].search(
            ['|',
             ('name', '=', 'New'),
             ('name', '=', 'In Progress')
             ])
        claims = env['crm.claim'].search([('stage_id', 'in', stages.ids)])

        customers = claims.mapped('partner_id')

        if search:
            customers = customers.filtered(
                lambda partner: search.lower() in partner.display_name.lower())

        inbound_customers = []
        for customer in customers:
            inbound_customers.append({
                'id': customer.id,
                'name': customer.name,
            })

        return {
            'status': 'ok',
            'customers': inbound_customers,
        }

    @http.route('/rma_screen/get_products', type='json', auth='user')
    def get_products(self, customer, search='', page=0,  **kw):
        cr = http.request.cr
        products = list()

        if not search:
            raise exceptions.ValidationError('You have to specify at least one character')

        search_limit = 30
        search_offset = page * search_limit
        search = '%%%s%%' % search

        cr.execute('''
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
''', [search, search, search, search, supplier_id, search_limit, search_offset])
        products_results = cr.fetchall()

        cr.execute('''
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
''', [search, search, search, search, supplier_id])

        products_count = cr.fetchall()

        for product in products_results:
            products.append({
                'id': product[0],
                'name': product[1],
                'image': '/web/binary/image?model=product.product&id=%s&field=image' % product[0]
            })

        results = {'status': 'ok',
                   'search_limit': search_limit,
                   'products': products,
                   'products_count': products_count[0][0]}
        return results

    @http.route('/rma_screen/get_product', type='json', auth='user')
    def get_product(self, id, supplier_id, **kw):
        env = http.request.env

        if not id or not supplier_id:
            print 'Problem'

        product = env['product.product'].browse(int(id))

        supplier = env['res.partner'].browse(int(supplier_id))

        # retrieve the partner and its child to search for supplier info
        supplier_childs = supplier.child_ids

        supplier_info = product.seller_ids.filtered(
            lambda r: r.name.id == supplier.id or
                      r.name.id in supplier_childs.ids)

        requires_unpack = supplier_info.requires_unpack
        requires_relabel = supplier_info.requires_relabel

        if len(supplier_info) != 1:
            results = {
                'status': 'error',
                'message': '''
There is more or less than one supplier info for this product:
product id: %s, supplier id: %s
''' % (product.id, supplier_id)
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
                'description': product.description or 'No description',
                'default_code': product.default_code,
                'supplier_code': supplier_info.product_code or 'N/A',
                'requires_unpack': requires_unpack,
                'requires_relabel': requires_relabel,
                'barcodes': barcodes,
                'image': '/web/binary/image?model=product.product&id=%s&field=image' % product.id,
            }
        }
        return results

    @http.route('/rma_screen/check_package_empty', type='json',
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

    @http.route('/rma_screen/search_customer_claims', type='json',
                auth='user')
    def search_customer_claims(self, customer_id):
        env = http.request.env

        stages = env['crm.claim.stage'].search(
            ['|',
             ('name', '=', 'New'),
             ('name', '=', 'In Progress')
             ])

        crm_claims = env['crm.claim'].search([
            ('partner_id', '=', int(customer_id)),
            ('stage_id', 'in', stages.ids),
        ])

        claims = []
        for claim in crm_claims:
            claims.append({'name': claim.code,
                           'id': claim.id, })

        return {'status': 'ok',
                'claims': claims}

    @http.route('/rma_screen/get_claim_move_lines', type='json',
                auth='user')
    def get_claim_move_lines(self, claim_ids=False):
        env = http.request.env
        claims = env['crm.claim'].browse(claim_ids)

        pickings = claims.mapped('picking_ids').filtered(
            lambda r: r.state == 'assigned')
        pickings = pickings.sorted(key=lambda pick: (pick.min_date, pick.id))

        lines = []
        for picking in pickings:
            for move_line in picking.move_lines.filtered(
                    lambda r: r.state == 'assigned'):

                lines.append({
                    'product_id': move_line.product_id.id,
                    'quantity': move_line.product_qty,
                    'id': move_line.id,
                    'picking_name': picking.name,
                    'product_name': move_line.product_id.name[0:20],
                    'progress_done': 0,
                    'quantity_already_scanned': 0,
                    'is_new': False,
                })

        return {'status': 'ok',
                'po_move_lines': lines}

    def get_receipt_picking_type(self):
        env = http.request.env

        picking_type_id = env['stock.picking.type'].search([
            ('is_rma_receipts', '=', True)
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

    @http.route('/rma_screen/change_user', type='http', auth='user')
    def change_user(self, **kw):
        http.request.session.logout(keep_db=True)
        http.request.session.authenticate(request.session.db, login=kw['login'],
                                     password=kw['password'])

    @http.route('/rma_screen/get_worklocations', type='json', auth='user')
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

    @http.route('/rma_screen/get_user', type='json', auth='user')
    def get_user(self, barcode='',  **kw):
        env = http.request.env
        domain = []

        if barcode:
            domain.append(('login_barcode', '=', barcode))

        user = env['res.users'].search(
            domain
        )

        if user:
            return {'status': 'ok',
                    'username': user.name,
                    'user_id': user.id,
                    'login': user.login,
                    'image': '/web/binary/image?model=res.users&id=%s&field=image_medium' % user.id}
        else:
            return {'status': 'error'}

    @http.route('/rma_screen/process_picking_line', type='json',
                auth='user')
    def process_picking_line(self, qty, picking_line_id, box_name,
                             packing_order_id, reason_id=False, cart_id=False):
        env = http.request.env
        picking_line = env['stock.move'].browse(int(picking_line_id))

        destination = self.process_transfer(qty, picking_line, box_name)

        picking_line.write({'packing_order_id': packing_order_id,
                            'reason_id': reason_id})

        dest_list = self.get_destinations(destination)

        if filter(lambda dest: dest['id'] == cart_id, dest_list):
            destination_id = cart_id
        else:
            destination_id = dest_list[0]['id']

        destination = self.move_to_destination(box_name, destination_id)

        return {'status': 'ok',
                'destination': destination['destination']}

    def process_transfer(self, qty, picking_line, box_name):
        env = http.request.env
        picking = picking_line.picking_id

        result = picking.do_enter_transfer_details()
        wizard_id = result['res_id']
        my_wizard = env['stock.transfer_details'].browse(wizard_id)
        my_wizard_items = my_wizard.item_ids

        dest_package = self.search_dest_package(box_name)

        for wizard_line in my_wizard_items:
            if wizard_line.product_id == picking_line.product_id:
                # find a line we can validate
                wizard_line.result_package_id = dest_package.id
                wizard_line.quantity = qty
                needed_line = wizard_line
                break

        # unlink all other lines (since we only transfer one line at a time)
        unwanted_lines = my_wizard_items.filtered(
            lambda r: r.id != needed_line.id)

        unwanted_lines.unlink()

        my_wizard.sudo().do_detailed_transfer()

        return picking_line.move_dest_id.location_dest_id

    def transfer_to_next_location(self, package, destination_id=False):
        env = http.request.env
        for quant in package.quant_ids:
            picking = quant.reservation_id.picking_id

            wizard_id = picking.do_enter_transfer_details()['res_id']
            wizard = env['stock.transfer_details'].browse(wizard_id)

            if destination_id:
                for packop in wizard.packop_ids:
                    packop.destinationloc_id = int(destination_id)

            wizard.sudo().do_detailed_transfer()

    def move_to_destination(self, box_name, destination_id, **kw):
        env = http.request.env
        package = self.search_dest_package(box_name)
        self.transfer_to_next_location(package, destination_id)

        destination = env['stock.location'].browse(int(destination_id))
        return {'status': 'ok',
                'destination': destination.name}

    def create_picking(self, customer_id, product_id, quantity):
        env = http.request.env

        picking_type_id = self.get_receipt_picking_type()

        picking = env['stock.picking'].create({
            'partner_id': int(customer_id),
            'picking_type_id': picking_type_id.id,
        })

        product = env['product.product'].browse(int(product_id))
        move_line = env['stock.move'].create({
            'product_id': product.id,
            'product_uom_qty': quantity,
            'picking_type_id': picking_type_id.id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'location_id': env.ref('stock.stock_location_customers').id,
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

    def add_packing_order_on_move(self, picking, packing_order_id, reason_id):
        for move in picking.move_lines:
            move.write({'packing_order_id': packing_order_id,
                        'reason_id': reason_id})

    @http.route('/rma_screen/create_packing_order', type='json', auth='user')
    def create_packing_order(self, **kw):
        env = http.request.env
        packing_order = env['stock.packing.order'].create({})
        return {'status': 'ok',
                'packing_reference': packing_order.name,
                'packing_id': packing_order.id,
                }

    @http.route('/rma_screen/save_packing_note', type='json', auth='user')
    def save_packing_note(self, packing_id, note, **kw):
        env = http.request.env
        packing_oder = env['stock.packing.order'].browse(int(packing_id))
        packing_oder.note = note
        return {'status': 'ok'}

    @http.route('/rma_screen/get_cart_list', type='json', auth='user')
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

    @http.route('/rma_screen/move_to_damaged', type='json', auth='user')
    def move_to_damaged(self, product_id, qty, reason, move_id, customer_id):
        env = http.request.env
        product_id = int(product_id)
        move = env['stock.move'].browse(int(move_id))
        product = env['product.product'].browse(product_id)

        if not move_id:
            picking, move = self.create_picking(customer_id,
                                                product_id, qty)

        scrap_obj = env['stock.move.scrap']
        move_scrap = scrap_obj.with_context(active_id=move.id).create({
            'product_id': product.id,
            'product_qty': int(qty),
            'product_uom': product.uom_id.id,
        })

        move_scrap.with_context(active_ids=[move.id]).move_scrap()

        return {
            'status': 'ok'
        }
