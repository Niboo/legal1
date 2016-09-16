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
            'user_email': env.user.partner_id.email,
        })

    @http.route('/rma_screen/get_customers', type='json', auth='user')
    def get_customers(self, search='',  **kw):
        env = http.request.env
        stage_new = env.ref('crm_claim.stage_claim1')
        stage_in_progress = env.ref('crm_claim.stage_claim5')
        stages = [stage_new.id, stage_in_progress.id]

        claims = env['crm.claim'].sudo().search([('stage_id', 'in', stages),
                                          ('picking_ids', '!=', False),
                                          ('picking_ids.state','=','assigned')])

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

    def search_products(self, products_results, search):
        search = search.lower()
        products = []
        for product in products_results.sorted(lambda p: p.id):
            if product.default_code and search in product.default_code.lower()\
                    or product.ean13 and search in product.ean13.lower() \
                    or product.name and search in product.name.lower():
                products.append({
                    'id': product.id,
                    'name': product.name,
                    'image': '/web/binary/image?model=product.product&id=%s&field=image' % product.id
                })
        return products

    @http.route('/rma_screen/get_products', type='json', auth='user')
    def get_products(self, claim_move_lines, search='', page=0,  **kw):
        env = http.request.env

        if not search:
            raise exceptions.ValidationError(
                'You have to specify at least one character')

        products_results = env['product.product']
        for line in claim_move_lines:
            products_results |= env['product.product'].browse(
                int(line['product_id']))

        return {
            'status': 'ok',
            'products': self.search_products(products_results, search),
        }

    @http.route('/rma_screen/get_product', type='json', auth='user')
    def get_product(self, id, **kw):
        env = http.request.env

        if not id:
            print 'Problem'

        product = env['product.product'].browse(int(id))

        return {
            'status': 'ok',
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description or 'No description',
                'default_code': product.default_code,
                'supplier_code': 'N/A',
                'barcodes': [product.ean13 or ''],
                'image': '/web/binary/image?model=product.product&id=%s&field=image' % product.id,
            }
        }

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

        stage_new = env.ref('crm_claim.stage_claim1')
        stage_in_progress = env.ref('crm_claim.stage_claim5')
        stages = [stage_new.id, stage_in_progress.id]

        crm_claims = env['crm.claim'].sudo().search([
            ('partner_id', '=', int(customer_id)),
            ('stage_id', 'in', stages),
        ])

        claims = []
        for claim in crm_claims:
            if claim.picking_ids.filtered(
                lambda picking: picking.state == 'assigned'):
                claims.append({'name': claim.code,
                               'id': claim.id, })

        return {'status': 'ok',
                'claims': claims}

    @http.route('/rma_screen/get_claim_move_lines', type='json',
                auth='user')
    def get_claim_move_lines(self, claim_ids=False):
        env = http.request.env
        claims = env['crm.claim'].sudo().browse(claim_ids)

        pickings = claims.mapped('picking_ids').filtered(
            lambda r: r.state == 'assigned')
        pickings = pickings.sorted(key=lambda pick: (pick.min_date, pick.id))

        lines = []
        for picking in pickings:
            for move_line in picking.move_lines:
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
                'claim_move_lines': lines}

    @http.route('/rma_screen/get_damage_reasons', type='json', auth="user")
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

        self.process_transfer(qty, picking_line, box_name)

        picking_line.write({'packing_order_id': packing_order_id,
                            'reason_id': reason_id})

        claim_domain = [('picking_ids','in',[picking_line.picking_id.id])]
        claim = env['crm.claim'].search(claim_domain)

        domain = [('picking_id.group_id', '=', claim.group_id.id),
                  ('product_id','=',picking_line.product_id.id),
                  ('picking_id.state','in',['confirmed', 'assigned'])]

        move = env['stock.move'].search(domain)

        if move:
            destination = move.location_dest_id
            move.action_assign()

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
        picking_line.product_uom_qty = qty

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
