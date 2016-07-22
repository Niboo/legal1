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
    	init: function (supplier_id, purchase_orders, purchase_order_lines) {
            this._super();
            var self = this;
            self.carts = {};
            self.current_cart = false;
            self.template = 'product_selector';
            self.supplier_id = supplier_id;
            self.received_products = {};
            self.product_in_package= {};
            self.purchase_orders = purchase_orders;
            self.purchase_order_lines = purchase_order_lines;
            self.closed_boxes = [];
        },
        start: function(){
            this._super();
            var self = this;

            self.$elem = $(QWeb.render(self.template,{
                'po_lines': self.purchase_order_lines,
            }));

            $('#content').html(self.$elem);
            self.search = '';
            self.add_listener_on_search();
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
                self.go_to_product(product_id);
            })
        },
        get_purchase_orders: function(product_id, qty) {
            var self = this;
            self.session.rpc('/inbound_screen/search_supplier_purchase', {
                supplier: self.supplier_id,
            }).then(function (data) {
                if (data.status == 'ok') {
                    var modal = new instance.stock_irm.modal.purchase_order_modal(self);
                    modal.start(data.orders, product_id, qty);
                } else {
                    var modal = new instance.stock_irm.modal.exception_modal();
                    modal.start(data.error, data.message);
                }
            });
        },
        add_listener_on_confirm_button: function(){
            var self = this;

            self.$nav.off('click.confirm');
            self.$nav.on('click.confirm', '#confirm a', function(event){
                self.get_purchase_orders();
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
        add_product: function(product_id, qty){
            var self = this;
            var list_cart_with_product = {};
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
                list_cart_with_product = self.received_products[product_id];
            } else {
                self.received_products[product_id] = list_cart_with_product;
            }

            // check if the received product already exist in the current cart
            if (_.has(list_cart_with_product, self.current_cart.id)) {
                var current_cart = list_cart_with_product[self.current_cart.id]

                if (_.has(current_cart, self.current_package_barcode)) {
                    var current_package = current_cart[self.current_package_barcode]

                    cart_box_list = current_package;
                }else{
                    list_cart_with_product[self.current_cart.id][self.current_package_barcode] = cart_box_list;
                }
            } else {
                list_cart_with_product[self.current_cart.id] = {};
                list_cart_with_product[self.current_cart.id][self.current_package_barcode] = cart_box_list;
            }

            if (!_.isEmpty(cart_box_list)){
                index = cart_box_list['index'];
                quantity = cart_box_list[index];
            } else {
                index = self.current_cart.box_index;
                cart_box_list['index'] = index;
                cart_box_list['package_barcode'] = self.current_package_barcode;
                cart_box_list['product_in_box'] = product_id;
                self.product_in_package[self.current_package_barcode] = product_id;
            }

            quantity += qty;
            cart_box_list[index] = quantity;



            // search an existing PO line and fill it if possible. If not, create a new one or retrieve a newly created one.
            var po_line = $.grep(self.purchase_order_lines, function(e){ return e.product_id == product_id && e.progress_done != 100.0; })[0];

            if(po_line){
                // we found a line we are able to fill!
                po_line.quantity_already_scanned += qty;
                po_line.progress_done = 100.0/po_line.quantity*po_line.quantity_already_scanned;

            }else{
                var created_line = $.grep(self.purchase_order_lines, function(e){ return e.product_id == product_id && e.is_new == true; })[0];

                if(created_line){
                    created_line.quantity+=qty;
                }else{
                    self.session.rpc('/inbound_screen/get_product_name', {
                        product_id: product_id
                    }).then(function(data){
                        if(data.status == "ok"){
                            self.purchase_order_lines.push({
                                'product_id':product_id,
                                'quantity': quantity,
                                'id': 0,
                                'product_name': data.product_name,
                                'progress_done': 100,
                                'quantity_already_scanned': quantity,
                                'is_new': true,
                            });
                        }
                    });
                }
            }
        },
        get_already_used_box: function(product_id){
            var self = this;
            var index = false;

            if (_.has(self.received_products, product_id)) {
                var product = self.received_products[product_id];

                if (_.has(product, self.current_cart.id)){

                    var cart_box_list = product[self.current_cart.id]

                    $.each(cart_box_list, function(key, value){
                        if(value.product_in_box == product_id && $.inArray(self.closed_boxes, value.package_barcode)==-1) {
                            index = value['index'];
                            //save the current package barcode since we may "come back" from another package
                            self.current_package_barcode=value['package_barcode']
                        }
                    });
                }
            }
            return index;
        },
        set_box_barcode: function(barcode){
            var self = this;
            self.current_package_barcode = barcode;
        },
        select_cart: function(cart_id, cart_name){
            var self = this;
            var cart = {
                name: cart_name,
                id: cart_id,
                box_index: 1
            }
            if (_.has(self.carts, cart_id)) {
                cart = self.carts[cart_id];
            } else {
                self.carts[cart_id] = cart;
            }

            self.current_cart = cart;
        },
        confirm: function(note) {
            var self = this;

            var uncomplete_order_line = $.grep(self.purchase_order_lines, function(a){ return a.is_new != false && a.quantity_already_scanned != a.quantity});
            var unordered_product = $.grep(self.purchase_order_lines, function(a){ return a.is_new == true});

            if(uncomplete_order_line.length > 0){
                //todo: check if a box exist for that po!
                var modal = new instance.stock_irm.modal.box_barcode_modal_staging();
                modal.start(uncomplete_order_line);
            }

            if(unordered_product.length > 0){
                //todo: do something with them :D
                console.log(unordered_product)
            }

            //self.session.rpc('/inbound_screen/process_picking', {
            //    supplier_id: self.supplier_id,
            //    results: self.received_products,
            //    note: note,
            //    purchase_orders: self.purchase_orders
            //}).then(function(data){
            //    if (data.status == 'ok'){
            //        var modal = new instance.stock_irm.modal.confirmed_modal();
            //        modal.start();
            //        window.setTimeout(function(){
            //            window.location.href = "/inbound_screen";
            //        }, 3000);
            //    } else {
            //        var modal = new instance.stock_irm.modal.exception_modal();
            //        modal.start(data.error, data.message);
            //    }
            //}).fail(function(data){
            //    var modal = new instance.stock_irm.modal.exception_modal();
            //    modal.start(data.data.arguments[0], data.data.arguments[1]);
            //});
        },
        process_barcode: function(barcode) {
            var self = this;
            self.search = barcode.replace(/[\s]*/g, '');
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
        },
        update_po_lines: function(){
            var self = this;
            $result = $(QWeb.render("inbound_line_list",{
                'po_lines': self.purchase_order_lines
            }));

            $('#po-lines-list').html($result);
        },
        go_to_product: function(product_id){
            var self = this;
            var ProductPage = instance.stock_irm.inbound_product_page;

            self.$elem = $(QWeb.render(self.template,{
                'po_lines': self.purchase_order_lines,
            }));

            self.product_page = new ProductPage(self, product_id);
            self.product_page.start();

            // reorder the boxes so the one with the current product are at the top
            var po_line_with_current_product = $.grep(self.purchase_order_lines, function(a){ return a.product_id == product_id});
            var po_line_without_current_product = $.grep(self.purchase_order_lines, function(e){ return e.product_id != product_id});

            self.purchase_order_lines = po_line_with_current_product.concat(po_line_without_current_product);
        },

    });

    instance.stock_irm.inbound_product_picking = inbound_product_picking;

})();
