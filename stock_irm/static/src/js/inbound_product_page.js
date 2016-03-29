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
    var current_cart_id;
    var current_cart_name;
    var current_cart_boxes;
    var cart_boxes_content = []
    var next_box_index;

    var inbound_product_page = instance.stock_irm.widget.extend({
    	init: function (parent, id) {
            this._super();
            var self = this;
            self.id = id;
            self.template = 'product_page';
            self.parent = parent;
        },
        start: function(){
            var self = this;
            self.get_product();
            self.next_box_index = 0;
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
            self.$elem.find("button[data-target='#cartSelectionModal']").click(function(){
                self.get_carts();
            })

            //add buttons for test purposes (they are used to add items on the cart, since i don't have a barcode scanner...)
            self.$elem.find("#add_prod_1").click(function(){
                self.add_product_to_cart(1)
            })
            self.$elem.find("#add_prod_2").click(function(){
                self.add_product_to_cart(2)
            })
            self.$elem.find("#add_prod_3").click(function(){
                self.add_product_to_cart(3)
            })
        },
        get_product: function(){
            var self = this;
            self.session.rpc('/inbound_screen/get_product', {
                id: self.id,
                supplier_id: self.parent.supplier_id
            }).then(function(data){
                self.$elem = $(QWeb.render(self.template, {
                    product: '/stock_irm/static/img/product1.jpg',
                    product: data.product
                }));
                $('body').html(self.$elem);
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
                var $result = $(QWeb.render('carts_result', {
                    carts: self.carts,
                }));

                self.$elem.find('#cartlist').html($result);
                self.add_listener_on_carts();
                self.$elem.find('#cartSelectionModal').modal("show");
            });
            self.$elem.find("button[data-target='#cartSelectionModal']").html("Change Cart")
        },
        add_listener_on_carts: function(){
            // when we select a cart, we retrieve its list of locations
            var self = this;

            $('#cartlist a').click(function(event){
                self.current_cart_id = $(event.currentTarget).attr('cart-id');
                self.current_cart_name = $(event.currentTarget).attr('cart-name');

                self.session.rpc('/inbound_screen/get_cart_boxes', {
                    cart_id: self.current_cart_id,
                }).then(function(data){
                    self.current_cart_boxes = data.cart_boxes;
                });

                $('#cartSelectionModal').modal('toggle');
            })
        },
        add_product_to_cart: function(product_id){
            var self = this;
            var qty = parseInt(self.$elem.find('#quantity input').val())

            if(cart_boxes_content[product_id.toString()] == undefined){
                try{
                    // save needed information about location, quantity, etc
                    cart_boxes_content[product_id.toString()] = {'product_id': product_id,
                        'cart_name':self.current_cart_name,
                        'cart_id':self.current_cart_id,
                        'location_name':self.current_cart_boxes[self.next_box_index]['name'],
                        'location_id':self.current_cart_boxes[self.next_box_index]['id'],
                        'quantity':qty
                    };
                    self.next_box_index += 1;

                }catch(err){
                    //todo: better solution than an alert
                    alert("No more location seems to be available for this cart");
                }
            }else{
                cart_boxes_content[product_id.toString()]['quantity'] += qty;
            }

            //display where to store the item
            $('#rack').html("<span>Put it in "+cart_boxes_content[product_id.toString()]['cart_name']+" / "+cart_boxes_content[product_id.toString()]['location_name']+"</span>");

            //reset the quantity to 1
            self.$elem.find('#quantity input').val(parseInt(1));
        }
    });

    instance.stock_irm.inbound_product_page = inbound_product_page;

})();
