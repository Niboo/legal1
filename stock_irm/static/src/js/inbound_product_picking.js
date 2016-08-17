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
            this._super();
            var self = this;
            self.template = 'product_selector';
            self.supplier_id = supplier_id;
            self.po_ids = po_ids;
            self.po_move_lines = po_move_lines;
            self.closed_boxes = [];
        },
        start: function(){
            this._super();
            var self = this;

            self.get_printer_ip();

            var po_move_lines_by_picking = _.groupBy(self.po_move_lines, function(po_move_line){
                return po_move_line.picking_name;
            });
            self.$elem = $(QWeb.render(self.template,{
                'po_lines': po_move_lines_by_picking,
            }));

            $('#content').html(self.$elem);
            self.search = '';
            self.add_listener_on_search();
            self.add_listener_on_confirm_button();
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
            self.add_listener_on_confirm_button()
        },
        add_listener_on_search: function(){
            var self = this;
            // Do the search when clicking on the button
            self.$elem.find('#search_bar + span button').click(function (event) {
                self.do_search();
            });
            // Do the search when typing more than 5 letters
            self.$elem.find('#search_bar').keyup(function (event) {
                if (event.currentTarget.value.length > 5 | event.which == 13) {
                    self.do_search();
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
                self.get_products();
            }
        },
        process_barcode: function(barcode) {
            var self = this;
            self.search = barcode.replace(/[\s]*/g, '');
            self.page = 1;
            self.$elem.find('#results').empty();
            self.get_products();
        },
        add_listener_on_more: function(){
            var self = this;

            self.$elem.find('#more').click(function(event){
                event.preventDefault();
                self.page += 1;
                self.get_products();
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
        add_listener_on_confirm_button: function(){
            var self = this;
            self.$nav.off('click.confirm');
            self.$nav.on('click.confirm', '#confirm a', function(event){
                var modal = new instance.stock_irm.modal.confirm_note_modal();
                modal.start(self);
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
        get_products: function(){
            var self = this;
            self.session.rpc('/inbound_screen/get_products', {
                supplier_id: self.supplier_id,
                search: self.search,
                page: self.page - 1
            }).then(function(data){
                self.products = data.products;

                if (self.products.length == 1){
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
                console.log('yes!');
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
                modal.start();
            }
        },
        set_box: function(box, move_line, callback) {
            var self = this;
            self.current_move_line = move_line;
            self.current_move_line.box = box;

            if (callback!==undefined) {
                callback.do_after_set_box(box, move_line);
            }
        },
        add_product: function(product, qty, move_line){
            var self = this;

            if(!move_line.is_new) {
                var move_quantity_left = move_line.quantity - move_line.quantity_already_scanned
                if (move_quantity_left > qty) {
                    move_line.quantity_already_scanned += qty;
                    self.start();
                    return
                }

                if (move_quantity_left == qty) {
                    move_line.quantity_already_scanned += qty;
                    var modal = new instance.stock_irm.modal.validate_po_line_modal();
                    modal.start(self, 0, move_line);
                    return
                }

                if (move_quantity_left < qty) {
                    move_line.quantity_already_scanned += move_quantity_left;
                    qty -= move_quantity_left;
                    var modal = new instance.stock_irm.modal.validate_po_line_modal();
                    modal.start(self, qty, move_line, product);
                    return
                }
            } else {
                move_line.quantity_already_scanned += qty;
                self.start();
                return
            }
        },
        confirm: function(note) {
            var self = this;
            console.log('test');
            var uncomplete_order_line = $.grep(self.po_move_lines, function(a){ return a.is_new == false && a.quantity_already_scanned > 0 && a.quantity_already_scanned != a.quantity});
            var unordered_product = $.grep(self.po_move_lines, function(a){ return a.is_new == true});

            var staging_id = $('#change-worklocation').attr('data-staging-id')


            if(unordered_product.length > 0) {
                self.session.rpc('/inbound_screen/create_picking_for_unordered_lines', {
                    extra_lines: unordered_product,
                    dest_box_id: staging_id,
                    supplier_id: self.supplier_id,
                }).then(function (data) {
                    if (data.status != 'ok') {
                        var modal = new instance.stock_irm.modal.exception_modal();
                        modal.start(data.error, data.message);
                    }
                });
            }

            if(uncomplete_order_line.length > 0) {
                _.each(uncomplete_order_line, function (line) {
                    self.session.rpc('/inbound_screen/process_incomplete_picking_line', {
                        'qty': line.quantity_already_scanned,
                        'picking_line_id': line.id,
                        'box_name': line.box,
                    }).then(function (data) {
                        if (data.status != 'ok') {
                            var modal = new instance.stock_irm.modal.exception_modal();
                            modal.start(data.error, data.message);
                        }
                    })
                })
            }

            var modal = new instance.stock_irm.modal.confirmed_modal();
            modal.start();
            window.setTimeout(function(){
                window.location.href = "/inbound_screen";
            }, 5000);
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
    });

    instance.stock_irm.inbound_product_picking = inbound_product_picking;

})();
