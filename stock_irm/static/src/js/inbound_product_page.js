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
                qty = $('#quantity input').val();
                if($(event.currentTarget).attr('data-dir') == 'up'){
                    $('#quantity input').val(parseInt(qty) + 1);
                } else {
                    if(qty > 1){
                        $('#quantity input').val(parseInt(qty) - 1);
                    }
                }
            });
        },
        add_listener_on_cart_button: function(){
            var self = this;
            self.$elem.find("div[data-target='#cartSelectionModal']").click(function(){
                self.get_carts();
            })
        },
        get_product: function(){
            var self = this;
            self.session.rpc('/inbound_screen/get_product', {
                id: self.id,
                supplier_id: self.parent.supplier_id
            }).then(function(data){
                var cart_id;
                var box_id;
                var quantity;
                var cart_with_product = []

                // building the array with the needed information
                if(self.parent.received_products[self.id]){
                    $.each( self.parent.received_products[self.id], function( key, value ) {
                        $.each(value, function(key, value){
                            if(key!="index"){
                                box_id = key;
                                quantity = value;
                            }
                        });
                        cart_with_product.push({"cart_name":self.parent.carts[key]["name"], "box": box_id, "quantity":quantity});
                    });
                }

                self.product = data.product;
                self.$elem = $(QWeb.render(self.template, {
                    product: self.product,
                    quantity: self.quantity,
                    barcodes: data.product.barcodes,
                    list_cart_with_product: cart_with_product || []
                }));
                self.barcodes = data.product.barcodes;
                $('#content').html(self.$elem);

                if (self.parent.current_cart) {
                    self.display_cart_info();
                }

                self.add_listener_on_quantity();
                self.add_listener_on_cart_button();
            })
        },
        get_carts: function(){
            //retrieve the carts and fill the modal page
            var self = this;

            self.session.rpc('/inbound_screen/get_carts', {
            }).then(function(data){
                self.carts = data.carts;
                var $result = $(QWeb.render('cart_result', {
                    carts: self.carts,
                }));

                self.show_modal('Cart Selection', $result);
                self.add_listener_on_carts();
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
            })
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
            self.$nav.on('click.search', '#search a', function(event){
                var qty = self.$elem.find('#quantity input').get(0).value
                self.parent.add_product(self.id, parseInt(qty));
                self.destroy();
                self.parent.start();
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

            self.$nav.find('#confirm a').show();
            self.$nav.off('click.confirm');
            self.$nav.on('click.confirm', '#confirm a', function(event){
                var qty = self.$elem.find('#quantity input').get(0).value
                self.parent.add_product(self.id, parseInt(qty));
                self.parent.confirm();
            })
        },
        destroy: function(){
            this._super();
        },
        process_barcode: function(barcode) {
            var self = this;
            var qty = self.$elem.find('#quantity input').get(0).value;

            if(!_.contains(self.barcodes, barcode.replace(/[\n\r]+/g, ''))){
                //if we scanned another product, then add the previous product before processing the barcode
                self.parent.start();
                self.parent.add_product(self.id, parseInt(qty));
                self.parent.process_barcode(barcode);
                self.destroy();
            }else{
                //if we scanned the same product, simply update the quantity
                qty++;
                self.$elem.find('#quantity input').get(0).value = qty;
            }
        },
    });

    instance.stock_irm.inbound_product_page = inbound_product_page;

})();
