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
    	init: function (supplier_id) {
            this._super();
            var self = this;
            self.carts = {};
            self.current_cart = false;
            self.template = 'product_selector';
            self.supplier_id = supplier_id;
            self.received_products = {};
        },
        start: function(){
            var self = this;
            self.$elem = $(QWeb.render(this.template));
            $('#content').html(self.$elem);
            self.search = '';
            self.add_listener_on_search();
            self.add_listeners();
            self.get_printer_ip();
        },
        get_printer_ip: function(){
            var self = this;
            self.session.rpc('/inbound_screen/get_printer_ip')
                .then(function(data){
                if(data.status == 'ok'){
                    self.printer_ip = data.printer_ip;
                }
            });
        },
        refresh: function(){
            var self = this;
            $('#content').html(self.$elem);
            self.add_listeners();
            self.add_listener_on_search();
            self.add_listener_on_product();
            self.add_listener_on_more();
        },
        add_listener_on_search: function(){
            var self = this;
            self.$elem.find('#search_bar + span button').click(function (event) {
                self.do_search();
            });
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
                var ProductPage = instance.stock_irm.inbound_product_page;
                self.product_page = new ProductPage(self, product_id);
                self.product_page.start();
            })
        },
        add_listener_on_confirm_button: function(){
            var self = this;

            if (_.isEmpty(self.received_products)) {

            } else {
                self.$nav.off('click.confirm');
                self.$nav.on('click.confirm', '#confirm a', function(event){
                    self.confirm();
                })
            }
        },
        add_listener_on_back_button: function(){
            var self = this;
            self.$nav.find('#back a').show();
            self.$nav.off('click.back');
            self.$nav.on('click.back', '#back a', function(event){
                var $result = $(QWeb.render('go_back'));
                self.show_modal('Are you sure you want to go back?', 'All your change will be canceled', $result, false);
                self.add_listener_on_goback_button();
                self.add_listener_on_continue_button();
            })
        },
        add_listener_on_ask_close: function(){
            var self = this;
            self.$elem.find("div[data-target='#closeBoxModal']").click(function(){
                self.propose_close();
            })
        },
        add_listener_on_goback_button: function(){
            var self = this;
            self.$modal.find('#close').click(function(event){
                self.$modal.modal('hide');
                window.location.href = "/inbound_screen";
            })
        },
        add_listener_on_continue_button: function(){
            var self = this;
            self.$modal.find('#continue_picking').click(function(event){
                self.$modal.modal('hide');
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
                    var product_id = self.products[0].id;
                    var ProductPage = instance.stock_irm.inbound_product_page;
                    self.product_page = new ProductPage(self, product_id);
                    self.product_page.start();
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
        add_product: function(product_id, qty, product_name, barcode){
            var self = this;
            var product = {};
            var cart_box_list = {};
            var quantity = 0;
            var index;

            // we book the cart only when adding a product (to avoid booking when missclicking)
            self.session.rpc('/inbound_screen/book_cart', {
                cart_id: self.current_cart.id,
            });

            // check if we already have the product id in our received products
            // product is a list of the carts in which the product exists
            if (_.has(self.received_products, product_id)) {
                product = self.received_products[product_id];
            } else {
                self.received_products[product_id] = product;
            }

            if (_.has(product, self.current_cart.id)) {
                cart_box_list = product[self.current_cart.id];
            } else {
                product[self.current_cart.id] = cart_box_list;
            }

            if (!_.isEmpty(cart_box_list)){
                index = cart_box_list['index'];
                quantity = cart_box_list[index];
            } else {
                index = self.current_cart.box_index;
                cart_box_list['index'] = index;
            }

            quantity += qty;
            cart_box_list[index] = quantity;
        },
        select_box: function(product_id, cart_selection){
            var self = this;
            if (_.has(self.received_products, product_id)) {
                var product = self.received_products[product_id];
                if (_.has(product, self.current_cart.id)) {
                    var cart = product[self.current_cart.id]
                    return cart['index'];
                }
            }
            if(!cart_selection){
                self.current_cart.box_index += 1;
            }
            return self.current_cart.box_index;
        },
        select_cart: function(cart_id, cart_name){
            var self = this;
            var cart = {
                name: cart_name,
                id: cart_id,
                box_index: 1,
            }

            if (_.has(self.carts, cart_id)) {
                cart = self.carts[cart_id];
            } else {
                self.carts[cart_id] = cart;
            }

            self.current_cart = cart;
        },
        confirm: function(purchase_orders) {
            var self = this;
            var $result = $(QWeb.render('confirm_inbound_modal'));
            var $footer = $(QWeb.render('confirm_note'));
            self.show_modal('Confirm this picking', $result, $footer, true);
            self.add_listener_on_close_button();
            self.add_listener_on_confirm_note_button(purchase_orders);
        },
        add_listener_on_close_button: function(){
            var self = this;
            $('#close').off('click.back');
            $('#close').on('click.back', function(event){
                self.$modal.modal('hide');
            })
        },
        add_listener_on_confirm_note_button: function(purchase_orders){
            var self = this;
            $('#confirm_note').off('click.confirm');
            $('#confirm_note').on('click.confirm', function (event) {
                self.session.rpc('/inbound_screen/process_picking', {
                    supplier_id: self.supplier_id,
                    results: self.received_products,
                    note: $('#packing_note').val(),
                    purchase_orders: purchase_orders,
                }).then(function(data){
                    if (data.status == 'ok'){
                        self.show_modal('Picking Confirmed!', "<i class='fa fa-check fa-10x' style='color:green'></i><b style='font-size: 2em'>Wait for redirection...</b>");
                        window.setTimeout(function(){
                            window.location.href = "/inbound_screen";
                        }, 3000);
                    } else {
                        var $result = $(QWeb.render('exception_modal',{
                            'error': data.error,
                            'message': data.message,
                        }));
                        self.show_modal('Print Error', $result, "", false);
                    }
                }).fail(function(data){
                    var $result = $(QWeb.render('exception_modal',{
                        'error': data.data.arguments[0],
                        'message': data.data.arguments[1],
                    }));
                    self.show_modal(data.message, $result, "", false);
                });
            })
        },
        process_barcode: function(barcode) {
            var self = this;
            self.search = barcode.replace(/[\n\r]+/g, '');
            self.page = 1;
            self.$elem.find('#results').empty();
            self.get_products();
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
        }
    });

    instance.stock_irm.inbound_product_picking = inbound_product_picking;

})();
