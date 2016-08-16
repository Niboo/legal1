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


class BandupController(http.Controller):
    @http.route('/bandup', type='http', auth="user")
    def bandup(self, **kw):
        # render the first template
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.bandup_screen', {
            'status': 'ok',
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'worklocation_id': current_user.work_location_id.id or 0,
            'title': 'Bandup',
        })

    @http.route('/bandup/get_package', type='json', auth="user")
    def get_package(self, barcode, **kw):
        env = http.request.env

        input_location = env.ref('stock.stock_location_company')

        # retrieve package information (product, quantity,...)
        scanned_package = env['stock.quant.package'].search(
            [('barcode', '=', str(barcode)),
             ('location_id', 'in', input_location._get_sublocations())
             ]
        )

        if not scanned_package:
            return{
                "status": "error",
                "error": "Error",
                "message": "Package could not be found",
            }

        if not scanned_package.quant_ids:
            return{
                "status": "error",
                "error": "Error",
                "message": "Package has no move",
            }

        if scanned_package.inbound_wave_id:
            return{
                "status": "error",
                "error": "Error",
                "message": "Package is already assigned to an inbound wave",
            }

        product = scanned_package.quant_ids[0].product_id

        total_qty = 0
        for quant in scanned_package.quant_ids:
            total_qty += quant.qty

        return {
            'status': 'ok',
            'scanned_package': {
                'id': scanned_package.id,
                'barcode': scanned_package.barcode,
                'name': scanned_package.name,
            },
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description or "No description",
                'quantity': total_qty,
                'image': "/web/binary/image?model=product.product&id=%s&field=image" % product.id,
            }
        }

    @http.route('/bandup/get_location', type='json', auth="user")
    def get_location(self, barcode, **kw):
        env = http.request.env

        # retrieve the scanned location
        location = env['stock.location'].search(
            [('barcode', '=', barcode)]
        )

        if not location:
            return {
                'status': 'error',
                'message': "No location has been found with this barcode"
            }

        return {
            'location_id': location.id,
            'location_name': location.name,
        }

    @http.route('/bandup/move_package', type='json', auth='user')
    def move_package(self, package_id, **kw):
        # method called after scanning the final location in the stock
        env = http.request.env

        try:
            package = env['stock.quant.package'].browse(package_id)
            self.transfer_package(package, False)
            return {'status': 'ok'}
        except BaseException as e:
            return {'status': 'error',
                    'error': type(e).__name__,
                    'message': str(e)}

    @http.route('/bandup/transfer_package_batch', type='json', auth="user")
    def transfer_package_batch(self, package_ids, **kw):
        # method called when clicking on "go to wave". It moves all scanned
        # packages from input to "bandup" location, and create the package list
        # that will be used in the inbound wave
        env = http.request.env

        try:
            inbound_wave = env['stock.inbound.wave'].create({
                'user_id': http.request.uid,
                'package_ids': [(6, False, package_ids)],
                'state': "in_progress"
            })

            package_list = []

            for package_id in package_ids:
                package = env['stock.quant.package'].browse(package_id)
                package = self.transfer_package(package, True)

                total_qty = 0
                for quant in package.quant_ids:
                    total_qty += quant.qty

                one_quant = package.quant_ids[0]
                picking = one_quant.reservation_id.picking_id
                stock_location = picking.location_dest_id
                putaway_strategy = env['stock.product.putaway.strategy'].search(
                    [
                        ('product_product_id', '=',
                         package.quant_ids[0].product_id.id),
                        ('fixed_location_id.id', 'in',
                         stock_location._get_sublocations())
                    ])
                dest_location = putaway_strategy.fixed_location_id or stock_location

                package_list.append({
                    'product_name': package.quant_ids[0].product_id.name,
                    'product_description': package.quant_ids[
                                               0].product_id.description or "No description",
                    'product_quantity': total_qty,
                    'location_name': dest_location.name,
                    'location_position': str(dest_location.posx) + " / " +
                                         str(dest_location.posy) + " / " +
                                         str(dest_location.posz),
                    'package_barcode': package.barcode,
                    'package_id': package.id,
                    'location_dest_barcode': dest_location.loc_barcode,
                    'product_image':
                        "/web/binary/image?model=product.product&id=%s&field=image"
                        % package.quant_ids[0].product_id.id,
                })

            return {
                'status': 'ok',
                'package_list': package_list,
            }

        except BaseException as e:
            return {'status': 'error',
                    'error': type(e).__name__,
                    'message': str(e)}


    def transfer_package(self, package, is_end_package_needed=True):
        env = http.request.env

        destination = False
        end_package = False

        for quant in package.quant_ids:
            picking = quant.reservation_id.picking_id

            result = picking.do_enter_transfer_details()
            wizard_id = result['res_id']
            wizard = env['stock.transfer_details'].browse(wizard_id)

            if not destination:
                item = wizard.item_ids.filtered(lambda r: r.package_id == package)
                packop = wizard.packop_ids.filtered(lambda r: r.package_id == package)

                destination = item and item.destinationloc_id or packop.destinationloc_id

                if destination.is_bandup_location == False \
                        and is_end_package_needed == True:
                    raise Exception("The location %s is not a bandup location."
                                    % destination.name)

                if is_end_package_needed:
                    end_package = self.search_dest_package(package.barcode, destination)
                    end_package.inbound_wave_id = package.inbound_wave_id

                if not destination:
                    destination = picking.location_dest_id

            # remove everything from the wizard

            wizard.write({
                'item_ids': [(5, False, False)],
                'packop_ids': [(5, False, False)]
            })

            # then create a new wizard item

            wizard_values = {
                    'package_id': package.id,
                    'product_id': quant.product_id.id,
                    'quantity': quant.qty,
                    'sourceloc_id': quant.location_id.id,
                    'destinationloc_id': destination.id,
                    'product_uom_id': quant.product_id.uom_id.id
                }

            if is_end_package_needed:
                # we shouldnt delete the end package in the last operation
                wizard_values['result_package_id'] = end_package.id,

            wizard.write({
                'item_ids': [(0, False, wizard_values)]
            })

            wizard.do_detailed_transfer()
        package.unlink()

        return end_package

    def search_dest_package(self, package_barcode, location):
        env = http.request.env

        dest_package = env['stock.quant.package'].search([
            ('barcode', '=', str(package_barcode)),
            ('location_id', '=', location.id)
        ])

        if not dest_package:
            dest_package = env['stock.quant.package'].create({
                'name': str(package_barcode),
                'barcode': str(package_barcode),
                'location_id': location.id,
            })

        return dest_package

    @http.route('/bandup/get_inbound_wave', type='json', auth="user")
    def get_inbound_wave(self, **kw):
        env = http.request.env

        wave_list = []

        waves = env['stock.inbound.wave'].search([
            ('user_id', '=', http.request.uid),
            ('state', '!=', 'done'),
        ])

        for wave in waves:
                wave_list.append({
                    'name': wave.id,
                    'id': wave.id,
                })

        results = {'status': 'ok',
                   'waves': wave_list,
                   }
        return results

    @http.route('/bandup/get_wave', type='json', auth="user")
    def get_wave(self, wave_id, **kw):
        env = http.request.env

        inbound_wave = env['stock.inbound.wave'].browse(int(wave_id))
        package_list = []

        bandup_locations = env['stock.location'].search([
            ('is_bandup_location', '=', True)
        ])

        for package in inbound_wave.package_ids.filtered(
                lambda r: r.location_id.id in bandup_locations.ids):

            total_qty = 0
            for quant in package.quant_ids:
                total_qty += quant.qty

            package_list.append({
                'product_name': package.quant_ids[0].product_id.name,
                'product_description': package.quant_ids[0].product_id.description,
                'product_quantity': total_qty,
                'location_name':"dummy for the moment",
                'package_barcode': package.barcode,
                'package_id': package.id,
                'location_dest_barcode': 'test',
                'product_image':
                     "/web/binary/image?model=product.product&id=%s&field=image"
                     % package.quant_ids[0].product_id.id,
            })

        return{
            'status': 'ok',
            'package_list': package_list,
        }
