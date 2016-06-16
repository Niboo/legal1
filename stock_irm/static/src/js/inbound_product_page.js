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
    	init: function (parent, id, quantity) {
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
            self.selected_purchases = [];
        },
        start: function(){
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
        },
        add_listener_on_print_button: function(){
            var self = this;
            self.$elem.find('#label-printed button').click(function(event){

                if ($(event.currentTarget).attr('data-dir') == 'print'){

                    if (self.quantity_to_print > 0 ){
                        self.parent.print_label(self.product.name, self.barcodes[0], self.quantity_to_print);
                        self.nb_already_printed += self.quantity_to_print;

                        $('#already_printed_quantity').val(self.nb_already_printed);
                        $('#quantity_to_print').val(0);
                        self.quantity_to_print = 0;

                        self.color_printed_labels(self.quantity_to_print);
                    }
                }
                $(':focus').blur()
            });
        },
        add_listener_on_cart_button: function(){
            var self = this;

            self.$elem.find("div[data-target='#cartSelectionModal']").click(function(){
                self.get_carts();
            })
        },
        add_listener_on_modal_print_button: function(){
            var self = this;

            self.$modal.find('#modal_print_button').click(function(event){
                event.preventDefault();

                self.parent.print_label(self.product.name, self.barcodes[0], self.quantity_to_print);
                self.$modal.modal('hide');
                self.nb_already_printed = self.nb_already_printed + self.quantity_to_print

                $('#already_printed_quantity').val(self.nb_already_printed);
                $('#quantity_to_print').val(0);
                self.quantity_to_print = 0;

                self.color_printed_labels(self.quantity_to_print);
                self.add_listener_for_barcode();
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
                            if(key!="index"){
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
                    var $result = $(QWeb.render('no_cart_message', {}));
                    self.show_modal('Cart Error', $result, '', true);
                }else{

                    var $result = $(QWeb.render('cart_result', {
                        carts: self.carts,
                    }));
                    var block_modal = true;
                    if(self.parent.current_cart){
                        block_modal = false;
                    }
                    self.show_modal('Cart Selection', $result, '', block_modal);
                    self.add_listener_on_carts();
                }
            });
        },
        add_listener_on_carts: function(){
            var self = this;
            self.$modal.find('.modal-body .cart').click(function(event){
                event.preventDefault();
                var cart_id = $(event.currentTarget).attr('cart-id');
                var cart_name = $(event.currentTarget).attr('cart-name');
                self.parent.select_cart(cart_id, cart_name)
                self.$modal.modal('hide');
                self.display_cart_info(true);
                self.add_listener_for_barcode();
            });
            $("a[is-in-usage='true']").hide()
            $('div.tags').find('input:checkbox').live('click', function () {
                if($('#display-all-cart').is(':checked')){
                    $("a[is-in-usage='true']").show()
                }else{
                    $("a[is-in-usage='true']").hide()
                }
            });
        },
        display_cart_info: function(cart_selection){
            if (typeof(cart_selection)==='undefined') cart_selection = false;
            var self = this;
            var cart = self.parent.current_cart;
            var box = self.parent.select_box(self.id, cart_selection);

            self.$elem.find('#rack').html('<span class="glyphicon glyphicon-arrow-right"></span> <span> ' + cart.name + ' / ' + box + '</span>');
        },
        add_listener_on_search_button: function(){
            var self = this;
            self.$nav.find('#search a').show();
            self.$nav.off('click.search');
            self.$nav.on('click.search', '#search a', function (event) {
                if(self.is_enough_label_printed()) {
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
                self.destroy();
                self.parent.refresh();
            })
        },
        add_listener_on_confirm_button: function(){
            var self = this;
            self.$nav.off('click.confirm');
            self.$nav.on('click.confirm', '#confirm a', function (event) {
                if(self.is_enough_label_printed()) {
                    var qty = self.$elem.find('#quantity input').get(0).value
                    self.parent.add_product(self.id, parseInt(qty));
                    self.$nav.off('click.confirm');
                    self.$nav.on('click.confirm', '#confirm a', function(event){
                        self.session.rpc('/inbound_screen/search_supplier_purchase', {
                            supplier: self.parent.supplier_id,
                        }).then(function(data){
                            if (data.status == 'ok'){
                                var $body = $(QWeb.render('supplier_purchase_orders',{
                                    'purchase_orders': data.orders,
                                }));
                                var $footer = $(QWeb.render('confirm_purchase_orders'));

                                self.show_modal("Select the impacted purchases orders",$body,$footer,true);
                                self.add_listener_on_purchase();
                                self.add_listener_on_footer();

                            } else {
                                //todo manage this
                            }
                        })

                    })
                }
            })
        },
        add_listener_on_purchase: function(){
            var self = this;
            $('.purchase-btn').click(function(event){
                var purchase_id = parseInt($(event.currentTarget).attr('purchase-id'));
                var index = self.selected_purchases.indexOf(purchase_id);

                if(index != -1){
                    self.selected_purchases.splice(index, 1);
                    $(event.currentTarget).removeClass('selected-purchase-btn');

                }else{
                    self.selected_purchases.push(purchase_id);
                    $(event.currentTarget).addClass('selected-purchase-btn');
                }
                if(self.selected_purchases.length>0){
                    $('#no_purchases').hide();
                    $('#select_purchases').show();
                }else{
                    $('#select_purchases').hide();
                    $('#no_purchases').show();
                }
            });
             $(':focus').blur()
        },
        add_listener_on_footer: function(){
            var self = this;
            $('#cancel').off('click.cancel');
            $('#cancel').on('click.cancel', function (event) {
                self.$modal.modal('hide');
            })
            $('#select_purchases').off('click.select_purchases');
            $('#select_purchases').on('click.select_purchases', function (event) {
                self.parent.confirm(self.selected_purchases);
            })
            $('#no_purchases').off('click.no_purchases');
            $('#no_purchases').on('click.no_purchases', function (event) {
                self.parent.confirm(false);
            })
        },
        destroy: function(){
            this._super();
        },
        process_barcode: function(barcode) {
            var self = this;
            var qty = self.$elem.find('#quantity input').get(0).value;

            if(!_.contains(self.barcodes, barcode.replace(/[\n\r]+/g, ''))){
                if(self.is_enough_label_printed()){
                   //if we scanned another product, then add the previous product before processing the barcode
                    self.parent.start();
                    self.parent.add_product(self.id, parseInt(qty));
                    self.parent.process_barcode(barcode);
                    self.destroy();
                }
            }else{
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
                var $result = $(QWeb.render('print_error_message', {}));
                self.show_modal('Not enough label printed', $result, '', false);
                self.add_listener_on_modal_print_button();
                return false;
            }else{
                return true;
            }
        },
    });

    instance.stock_irm.inbound_product_page = inbound_product_page;

})();
