///////////////////////////////////////////////////////////////////////////////
//
//    Author: Jérôme Guerriat
//    Copyright 2016 Niboo SPRL
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

    var inventory_page = instance.stock_irm.widget.extend({
        init: function () {
            this._super();
            var self = this;
            self.location_id = false;
            self.product_id = false;
            self.go_to_product = false;
            self.template = 'inventory_layout';
            QWeb.add_template('/stock_irm/static/src/xml/inventory.xml', function(){
                self.start();
            });


        },
        start: function() {
            var self = this;
            self._super();
            self.$elem = $(QWeb.render(self.template));
            $('#content').html(self.$elem);

            self.add_listener_for_barcode();
            self.add_listener_on_numpad();
        },
        add_listener_on_numpad: function(){
            var self = this;
            $('.num-pad .circle').off('click.numpad');
            $('.num-pad .circle').on('click.numpad', function (event) {
                var $target = $(event.currentTarget);
                value = $target.find("span").text();
                if(value=="C"){
                   $('#manual-barcode').val("");
                }else if(value=="Enter"){
                    self.process_barcode($('#manual-barcode').val());
                    $('#manual-barcode').val("");
                }else{
                    $('#manual-barcode').val($('#manual-barcode').val()+value);
                }
                $(':focus').blur()
            });
        },
        process_barcode: function(barcode) {
            var self = this;

            barcode = barcode.replace(/[\s]*/g, '');

            if(!self.location_id){
                self.session.rpc('/inventory_update/get_location', {
                    'barcode': barcode
                }).then(function(data){
                    if(data.status == "ok"){
                        self.$elem.find('#location_info').html("<h2>"+data.location_name+"</h2>")
                        self.location_id = data.location_id;
                        self.product_id = data.product.id;
                        self.go_to_product = true;
                        self.$elem.find('#message_box').switchClass("alert-warning", "alert-info", 100);
                        self.$elem.find('#message').html('Select quantity or scan product in this location');
                        self.$elem.find('#quantity_box').show();
                        self.$elem.find('#product_info').html($(QWeb.render('product_info', {
                            product: data.product
                        })));
                        self.$elem.find('#input_quantity').val("0");
                        self.add_listener_on_quantity();
                        self.add_listener_on_validate();
                    }else{
                        self.display_error('Error', data.message);
                    }
                });
            }else if(!self.product_id || self.go_to_product){
                self.session.rpc('/inventory_update/get_product', {
                    'barcode': barcode
                }).then(function(data){
                    if(data.status == "ok"){
                        self.product_id = data.product.id;
                        self.$elem.find('#message_box').switchClass("alert-info", "alert-success", 100);
                        self.$elem.find('#message').html('Please select the quantity');
                        self.$elem.find('#quantity_box').show();
                        self.$elem.find('#product_info').html($(QWeb.render('product_info', {
                            product: data.product
                        })));
                        self.$elem.find('#input_quantity').val("1");
                    }else{
                        self.display_error('Error', data.message);
                    }
                });
            }
        },

        add_listener_on_quantity: function(){
            var self = this;
            self.$elem.find('#quantity button').click(function(event){
                var qty = parseInt($('#quantity input').val());

                if($(event.currentTarget).attr('data-dir') == 'up'){
                    qty++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 0){
                        qty--;
                    }
                }
                $('#quantity input').val(qty);
                // force to lose focus to avoid adding +1 when scanning another product
                $(':focus').blur()
            });

            self.$elem.find('#quantity_to_print').keyup(function(event){
                $('#quantity_to_print').val(event.currentTarget.value);
                self.quantity_to_print = parseInt(event.currentTarget.value);
                self.color_printed_labels(self.quantity_to_print);
            })
        },

        add_listener_on_validate: function(){
            var self = this;
            self.$elem.find('#validate').show();
            self.$elem.find('#validate').click(function(event){
                var qty = parseInt(self.$elem.find('#input_quantity').val());


                self.session.rpc('/inventory_update/update_product_quantity', {
                    'product_id': self.product_id,
                    'location_id': self.location_id,
                    'quantity': qty,
                }).then(function(data){
                    if(data.status == "ok"){
                        var modal = new instance.stock_irm.modal.confirm_update_modal();
                        modal.start();
                        window.setTimeout(function(){
                            window.location.href = "/inventory_update";
                        }, 1500);
                    }
                });
            })

        }


    });

    instance.stock_irm.inventory_page = new inventory_page();
})();
