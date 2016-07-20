///////////////////////////////////////////////////////////////////////////////
//
//    Author: Samuel Lefever
//    Copyright 2015 Niboo SPRL
//
//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU Affero General Public License as
//    published by the Free Software Foundation, either version 3 of the
//    License, or (at your option) any later version.
//
//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU Affero General Public License for more details.
//
//    You should have received a copy of the GNU Affero General Public License
//    along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
///////////////////////////////////////////////////////////////////////////////

(function() {

    var instance = openerp;
    var _t = instance._t,
        _lt = instance._lt;
    var QWeb = instance.qweb;

    var inbound_product_picking = instance.stock_irm.widget.extend({
    	init: function (supplier_id, po_ids, po_move_lines) {
            var self = this;
            self._super('inbound_product_picking');
            self.template = 'product_selector';
            self.supplier_id = supplier_id;
            self.po_ids = po_ids;
            self.po_move_lines = po_move_lines;
            self.closed_boxes = [];
            self.session.rpc('/inbound_screen/create_packing_order').then(function(data){
                if(data.status == 'ok'){
                    self.packing_reference = data.packing_reference;
                    self.packing_id = data.packing_id;
                    var $elem = self.$nav.find('#packing-order-ref');
                    $elem.html(data.packing_reference);
                    $elem.attr('data-id', data.packing_id);
                    self.$nav.find('#packing-order-li').show();
                }
            });

        },
        start: function(){
            var self = this;
            self._super();
            self.get_printer_ip();

            var po_move_lines_by_picking = _.groupBy(self.po_move_lines, function(po_move_line){
                return po_move_line.picking_name;
            });
            self.$elem = $(QWeb.render(self.template,{
                'po_lines': po_move_lines_by_picking,
            }));
            if(self.cart === undefined){
                self.get_carts(true);
            }

            $('#content').html(self.$elem);
            self.search = '';
            self.add_listener_on_search();
            self.add_listener_on_confirm_button();
            self.add_listener_on_cart_select_button();
        },
        get_printer_ip: function(){
            var self = this;
            self.session.rpc('/inbound_screen/get_printer_ip').then(function(data){
                if(data.status == 'ok'){
                    self.printer_ip = data.printer_ip;
                }
            });
        },
        refresh: function(){
            var self = this;
            $('#content').html(self.$elem);
            self.add_listener_on_search();
            self.add_listener_on_product();
            self.add_listener_on_more();
            self.add_listener_on_confirm_button();
            self.add_listener_on_cart_select_button();
        },
        add_listener_on_search: function(){
            var self = this;
            var wait_for_search = false;
            // Do the search when clicking on the button
            self.$elem.find('#search_bar + span button').click(function (event) {
                self.do_search();
            });
            // Do the search when typing more than 5 letters or enter
            self.$elem.find('#search_bar').keyup(function (event) {
                if (event.which == 13){
                    self.do_search();
                }else{
                   if (wait_for_search == false) {
                       setTimeout(function() {
                           if (event.currentTarget.value.length > 5) {
                               self.do_search();
                           }
                           wait_for_search = false;
                       }, 500);
                   }
                   wait_for_search = true;
                }
                
            });
        },
        do_search: function(){
            var self = this;
            var search_value = self.$elem.find('#search_bar')[0].value;
            if (self.search != search_value & search_value!== undefined
                    & search_value.length >= 1){
                var self = this;
                self.page = 1;
                self.$elem.find('#results').empty();
                self.search = search_value;
                self.get_products(false);
            }
        },
        process_barcode: function(barcode) {
            var self = this;
            self.search = barcode.replace(/[\s]*/g, '');
            self.page = 1;
            self.$elem.find('#results').empty();
            self.get_products(true);
        },
        add_listener_on_more: function(){
            var self = this;

            self.$elem.find('#more').click(function(event){
                event.preventDefault();
                self.page += 1;
                self.get_products(false);
            })
        },
        add_listener_on_product: function($result){
            var self = this;
            if (!$result){
                $result = self.$elem.find('#results');
            }
            $result.find('a').click(function(event){
                var product_id = $(event.currentTarget).attr('data-id');
                self.go_to_product(product_id);
            })
        },
        confirm_po_move: function(){
            var self = this;
            var uncomplete_and_unexpected_move_line = _.filter(self.po_move_lines, function(move) {
                // Filter the lines that have not been scanned at all
                if(move.quantity_already_scanned == 0){
                    return false;
                }

                // Filter move that are completed
                if (move.quantity_already_scanned == move.quantity) {
                    return false;
                }
                return true;
            });

            if(uncomplete_and_unexpected_move_line.length > 0) {
                var modal = new instance.stock_irm.modal.confirm_move_modal(self, self.supplier_id, uncomplete_and_unexpected_move_line);
                modal.start();
            } else {
                var modal = new instance.stock_irm.modal.confirm_note_modal(self);
                modal.start();
            }
        },
        add_listener_on_confirm_button: function(){
            var self = this;
            self.$nav.off('click.confirm');
            self.$nav.on('click.confirm', '#confirm a', function(event){
                self.confirm_po_move();
            });
        },
        add_listener_on_back_button: function(){
            var self = this;
            self.$nav.find('#back a').show();
            self.$nav.off('click.back');
            self.$nav.on('click.back', '#back a', function(event){
                var modal = new instance.stock_irm.modal.back_modal();
                modal.start();
            })
        },
        get_products: function(skip_product_clic){
            var self = this;
            self.session.rpc('/inbound_screen/get_products', {
                supplier_id: self.supplier_id,
                search: self.search,
                page: self.page - 1
            }).then(function(data){
                self.products = data.products;

                if (self.products.length == 1 && skip_product_clic){
                    self.go_to_product(self.products[0].id);
                    return;
                }

                var $result = $(QWeb.render('product_result', {
                    products: self.products,
                }));

                self.add_listener_on_product($result);
                self.$elem.find('#results').append($result);
                self.$elem.find('#more').remove();

                if(data.products_count > data.search_limit * self.page){
                    var $more = $(QWeb.render('result_more', {}));
                    self.$elem.find('#results').append($more);
                    self.add_listener_on_more();
                }
            });
        },
        go_to_product: function(product_id){
            var self = this;
            var ProductPage = instance.stock_irm.inbound_product_page;

            self.product_page = new ProductPage(self, product_id);
            self.product_page.start();

            // reorder the boxes so the one with the current product are at the top
            var po_line_with_current_product = $.grep(self.po_move_lines, function(a){ return a.product_id == product_id});
            var po_line_without_current_product = $.grep(self.po_move_lines, function(e){ return e.product_id != product_id});

            self.po_move_lines = po_line_with_current_product.concat(po_line_without_current_product);
        },
        get_the_box: function(product, callback){
            var self = this;

            // Get the lines to treat for this product
            self.product_move_lines = _.filter(self.po_move_lines, function(po_move_line) {
                if(po_move_line.quantity_already_scanned == po_move_line.quantity) {
                    return false;
                }
                return po_move_line.product_id == product.id;
            });

            var move_line_from_po = _.filter(self.product_move_lines, function(move_line){
                return ! move_line.is_new;
            })
            if(move_line_from_po.length > 0){
                if(move_line_from_po[0].box!==undefined) {
                    self.set_box(move_line_from_po[0].box, move_line_from_po[0], callback)
                    return
                } else {
                    var modal = new instance.stock_irm.modal.box_barcode_modal(self, move_line_from_po[0], callback);
                    modal.start();
                    return
                }
            }

            var move_line_no_po = _.filter(self.product_move_lines, function(move_line){
                return move_line.is_new;
            })
            if(move_line_no_po.length == 1){
                self.set_box(move_line_no_po[0].box, move_line_no_po[0], callback)
            } else {
                var move_line = {
                    'product_id': product.id,
                    'quantity': 0,
                    'id': 0,
                    'product_name': product.name.substring(0,22),
                    'progress_done': 100,
                    'picking_name': '_',
                    'quantity_already_scanned': 0,
                    'is_new': true
                };
                self.po_move_lines.push(move_line);

                var modal = new instance.stock_irm.modal.box_barcode_modal(self, move_line, callback);
                // if creating extra box for leftover items, show cancel button
                if(callback.template == 'select_next_destination') {
                    modal.start(true);
                } else {
                    modal.start();
                }
            }
        },
        move_to_damaged: function(product_id, reason) {
            var self = this;
            self.session.rpc('/inbound_screen/move_to_damaged', {
                product_id: product_id,
                reason: reason,
            }).then(function(data){
                if (data.status == 'ok'){
                    var modal = new instance.stock_irm.modal.damage_confirmed_modal();
                    modal.start();
                    window.setTimeout(function(){
                        window.location.href = "/inbound_screen";
                    }, 3000);
                } else {
                    var modal = new instance.stock_irm.modal.exception_modal();
                    modal.start(data.error, data.message);
                }
            }).fail(function(data){
                var modal = new instance.stock_irm.modal.exception_modal();
                modal.start(data.data.arguments[0], data.data.arguments[1]);
            });
            return same_box_lines.length === 0;
        },
        set_box: function(box, move_line, callback) {
            var self = this;
            self.current_move_line = move_line;
            self.current_move_line.box = box;

            if (callback!==undefined) {
                callback.do_after_set_box(box, move_line);
            }
        },
        set_box_free: function(move_line) {
            var self = this;
            self.po_move_lines.splice(self.po_move_lines.indexOf(move_line),1);
        },
        update_progress: function(move_line) {
            var self = this;
            var qty = move_line.quantity;
            var qty_scanned = move_line.quantity_already_scanned;
            var percentage = 100 / qty * qty_scanned;
            move_line.progress_done = percentage;
            self.$elem.find("#"+move_line.id).css({"width":move_line.progress_done+'%'});
        },
        add_product: function(product, qty, move_line){
            var self = this;

            if(!move_line.is_new) {
                var move_quantity_left = move_line.quantity - move_line.quantity_already_scanned
                if (move_quantity_left > qty) {
                    move_line.quantity_already_scanned += qty;
                    self.update_progress(move_line);
                    self.start();
                    return
                }

                if (move_quantity_left == qty) {
                    move_line.quantity_already_scanned += qty;
                    self.update_progress(move_line);
                    var modal = new instance.stock_irm.modal.validate_po_line_modal();
                    modal.start(self, 0, move_line);
                    return
                }

                if (move_quantity_left < qty) {
                    move_line.quantity_already_scanned += move_quantity_left;
                    qty -= move_quantity_left;
                    self.update_progress(move_line);
                    var modal = new instance.stock_irm.modal.validate_po_line_modal();
                    window.setTimeout(function() {
                        modal.start(self, qty, move_line, product);
                    }, 500);
                    return
                }
            } else {
                move_line.quantity_already_scanned += qty;
                self.update_progress(move_line);
                self.start();
                return
            }
        },
        confirm: function(note) {
            var self = this;
            self.session.rpc('/inbound_screen/save_packing_note', {
                packing_id: self.packing_id,
                note: note,
            }).then(function (data) {
                if(data.status == 'ok'){
                    var modal = new instance.stock_irm.modal.confirmed_modal();
                    modal.start();
                    window.setTimeout(function(){
                        window.location.href = "/inbound_screen";
                    }, 2000);
                } else {
                    var modal = new instance.stock_irm.modal.exception_modal();
                    modal.start('Error', 'Packing note could not be saved');
                }
            });
        },
        print_label: function(product_name, barcode, quantity){
            if(this.printer_ip){
                try {
                    url = 'http://' + this.printer_ip + '/printer/wfmprint';
                    return $.ajax(url, {
                        dataType: 'xml',
                        data: {
                            'dev': "E",
                            'oname': "DYNAPPS",
                            'otype': "ZPL",
                            "FN11": product_name,
                            "FN12": barcode,
                            "PQ": quantity
                        },
                        context: {
                            url: url
                        }
                    });
                }
                catch(err){
                    console.log("Error during printing");
                }
            }else{
                console.log("No printer could be found");
            }
        },
        update_po_lines: function(){
            var self = this;
            var po_line_by_picking = _.groupBy(self.purchase_order_lines, function(po_line){
                return po_line.picking_name;
            });

            var $result = $(QWeb.render("inbound_line_list",{
                'po_lines': po_line_by_picking
            }));

            self.$elem.find('#po-lines-list').html($result);
        },
        get_carts: function (block_modal) {
            var self = this;
            self.session.rpc('/inbound_screen/get_cart_list', {}).then(function (data) {
                if(data.status == 'ok'){
                    var modal = new instance.stock_irm.modal.select_cart_modal(block_modal);
                    modal.start(self, data.carts);
                } else {
                    var modal = new instance.stock_irm.modal.exception_modal();
                    modal.start('Error', 'Could not retrieve the cart list');
                }
            });
        },
        set_cart: function (cart) {
            var self = this;
            self.cart = cart;
            self.$change_cart.html(QWeb.render('cart_navbar_item', {'cart': self.cart}));
        },
        add_listener_on_cart_select_button: function () {
            var self = this;
            self.$change_cart = self.$nav.find('#change-cart');
            self.$change_cart.show();
            self.$nav.off('click.change-cart');
            self.$nav.on('click.change-cart', '#change-cart a', function (e) {
                self.get_carts(false);
            });
        },
    });

    instance.stock_irm.inbound_product_picking = inbound_product_picking;

})();
