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

    var inbound_product_page = instance.stock_irm.widget.extend({
    	init: function (parent, id, quantity, packing_reference, packing_id) {
            this._super();
            var self = this;
            self.id = id;
            self.template = 'product_page';
            self.parent = parent;
            self.product;
            self.quantity = quantity;
            self.barcodes = [];
            self.nb_already_printed = 0;
            self.quantity_to_print = 0;
            self.packing_reference = packing_reference
            self.packing_id = packing_id
        },
        start: function(){
            this._super();
            var self = this;
            self.get_product();
            if (! self.parent.current_cart) {
                self.get_carts();
            }
        },
        add_listener_on_quantity: function(){
            var self = this;
            self.$elem.find('#quantity button').click(function(event){
                qty = parseInt($('#quantity input').val());

                if($(event.currentTarget).attr('data-dir') == 'up'){
                    qty++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 0){
                        qty--;
                    }
                }

                $('#quantity input').val(qty);

                if(qty-self.nb_already_printed >= 0){
                    self.quantity_to_print = qty-self.nb_already_printed
                    $('#quantity_to_print').val(self.quantity_to_print);
                }

                self.color_printed_labels(self.quantity_to_print);
                // force to lose focus to avoid adding +1 when scanning another product
                $(':focus').blur()
            });
        },
        add_listener_on_keyboard_quantity: function(){
            var self = this;

            $('#quantity_to_print').keyup(function(event){
                $('#quantity_to_print').val(event.currentTarget.value);
                self.quantity_to_print = parseInt(event.currentTarget.value);
                self.color_printed_labels(self.quantity_to_print);
            })
        },
        add_listener_on_label_quantity: function(){
            var self = this;
            self.$elem.find('#label-quantity button').click(function(event){
                qty = parseInt($('#label-quantity input').val());

                if($(event.currentTarget).attr('data-dir') == 'up'){
                    self.quantity_to_print++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 0){
                        self.quantity_to_print--;
                    }
                }

                $('#quantity_to_print').val(self.quantity_to_print);
                $(':focus').blur()
            });
            self.$elem.off("keyup.quantity");
            self.$elem.on('keyup.quantity', '#input_quantity', function (event) {
                self.quantity_to_print = parseInt($('#input_quantity').val()) - self.nb_already_printed;
                if(self.quantity_to_print>0){
                    $('#quantity_to_print').val(self.quantity_to_print);
                }else{
                    $('#quantity_to_print').val(0);
                }
                self.color_printed_labels(self.quantity_to_print);
            })

        },
        add_listener_on_print_button: function(){
            var self = this;
            self.$elem.find('#label-printed button').click(function(event){
                if ($(event.currentTarget).attr('data-dir') == 'print'){
                    if (self.quantity_to_print > 0 ){
                        self.print_missing_labels();
                    }
                }
                $(':focus').blur()
            });
        },
        print_missing_labels: function(){
            var self = this;
            self.parent.print_label(self.product.name, self.barcodes[0], self.quantity_to_print);
            self.nb_already_printed += self.quantity_to_print;

            $('#already_printed_quantity').val(self.nb_already_printed);
            $('#quantity_to_print').val(0);
            self.quantity_to_print = 0;

            self.color_printed_labels(self.quantity_to_print);
        },
        add_listener_on_cart_button: function(){
            var self = this;

            self.$elem.find("div[data-target='#cartSelectionModal']").click(function(){
                self.get_carts();
            })
        },
        color_printed_labels: function(missing_labels){
            var self = this;
            var color = "green";
            if(self.quantity_to_print>0){
                color = "red"
            }

            $('#print_button').css({'color':color});
            $('#already_printed_quantity').css({'color':color});
        },
        get_product: function(){
            var self = this;
            self.session.rpc('/inbound_screen/get_product', {
                id: self.id,
                supplier_id: self.parent.supplier_id
            }).then(function(data){
                
                var box_id;
                var quantity;
                var cart_with_product = new Array();

                // building the array with the needed information
                if(self.parent.received_products[self.id]){
                    $.each( self.parent.received_products[self.id], function( key, value ) {
                        $.each(value, function(key, value){
                            if(key!="index" && key!="package_barcode"){
                                box_id = key;
                                quantity = value;
                            }
                        });
                        cart_with_product.push({
                            "cart_name":self.parent.carts[key]["name"],
                            "box": box_id, "quantity":quantity});
                    });
                }

                self.product = data.product;
                self.$elem = $(QWeb.render(self.template, {
                    product: self.product,
                    quantity: self.quantity,
                    barcodes: data.product.barcodes,
                    packing_reference: self.packing_reference,
                    list_cart_with_product: cart_with_product
                }));
                self.barcodes = data.product.barcodes;
                $('#content').html(self.$elem);

                if (self.parent.current_cart) {
                    self.display_cart_info();
                }

                // print the label the first time
                self.parent.print_label(self.product.name, self.barcodes[0] , 1)
                self.nb_already_printed += 1;


                self.add_listener_on_quantity();
                self.add_listener_on_keyboard_quantity();
                self.add_listener_on_label_quantity();
                self.add_listener_on_cart_button();
                self.add_listener_on_print_button();
            })
        },
        get_carts: function(){
            //retrieve the carts and fill the modal page
            var self = this;

            self.session.rpc('/inbound_screen/get_carts', {
            }).then(function(data){
                self.carts = data.carts;
                if(self.carts.length == 0){
                    var modal = new instance.stock_irm.no_cart_modal();
                    modal.start();
                } else {
                    var block_modal = true;
                    if(self.parent.current_cart){
                        block_modal = false;
                    }
                    var modal = new instance.stock_irm.modal.select_cart_modal(self, block_modal);
                    modal.start(self.carts);
                }
            });
        },
        display_cart_info: function(cart_selection){
            if (typeof(cart_selection)==='undefined') cart_selection = false;
            var self = this;
            var cart = self.parent.current_cart;
            var box = self.select_box(self.id, cart_selection);

            self.$elem.find('#rack').html('<span class="glyphicon glyphicon-arrow-right"></span> <span> ' + cart.name + ' / ' + box + '</span>');
        },
        select_box: function(product_id, cart_selection){
            var self = this;
            var product_box = self.parent.get_already_used_box(product_id);
            if(product_box){
                return product_box;
            }else{
                var modal = new instance.stock_irm.modal.box_barcode_modal(self);
                modal.start();

                if(!cart_selection){
                    self.parent.current_cart.box_index += 1;
                }
                return self.parent.current_cart.box_index;
            }
        },
        add_listener_on_search_button: function(){
            var self = this;
            self.$nav.find('#search a').show();
            self.$nav.off('click.search');
            self.$nav.on('click.search', '#search a', function (event) {
                if(self.is_enough_label_printed()) {
                    $(':focus').blur()
                    var qty = self.$elem.find('#quantity input').get(0).value
                    self.parent.add_product(self.id, parseInt(qty));
                    self.destroy();
                    self.parent.start();
                }
            })
        },
        add_listener_on_back_button: function(){
            var self = this;
            self.$nav.find('#back a').show();
            self.$nav.off('click.back');
            self.$nav.on('click.back', '#back a', function(event){
                qty = parseInt($('#quantity input').val());
                product_image = $('#product_image').attr('src');

                var modal = new instance.stock_irm.modal.going_back_modal();
                modal.start(self, qty, product_image);
            })
        },
        add_listener_on_confirm_button: function(){
            var self = this;

            self.$nav.off('click.confirm');
            self.$nav.on('click.confirm', '#confirm a', function(event){
                if(self.is_enough_label_printed()){
                    var product_id = self.id
                    var qty = self.$elem.find('#quantity input').get(0).value;
                    self.parent.get_purchase_orders(product_id, qty);
                }
            });
        },
        destroy: function(){
            this._super();
        },
        process_barcode: function(barcode) {
            var self = this;
            var qty = self.$elem.find('#quantity input').get(0).value;

            if(!_.contains(self.barcodes, barcode.replace(/[\s]*/g, ''))){
                if(self.is_enough_label_printed()){
                   //if we scanned another product, then add the previous product before processing the barcode
                    self.parent.start();
                    self.parent.add_product(self.id, parseInt(qty));
                    self.parent.process_barcode(barcode);
                    self.destroy();
                }
            } else {
                //if we scanned the same product, simply update the quantity and print the label
                qty++;
                self.$elem.find('#quantity input').get(0).value = qty;

                // print the label each time we scan again
                self.parent.print_label(self.product.name, self.product.barcodes[0], 1)
                self.nb_already_printed += 1;
                $('#already_printed_quantity').val(self.nb_already_printed);

            }
        },
        is_enough_label_printed: function(){
            var self = this;
            if(self.quantity_to_print>0){
                var modal = new instance.stock_irm.modal.not_enough_label_modal(self)
                modal.start();
                return false;
            } else {
                return true;
            }
        },
    });

    instance.stock_irm.inbound_product_page = inbound_product_page;

})();
