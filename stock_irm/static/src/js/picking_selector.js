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
    instance.picking_waves = {}

    var picking_selector = instance.stock_irm.widget.extend({
    	init: function () {
            this._super();
            var self = this;

            QWeb.add_template('/stock_irm/static/src/xml/picking.xml', function(){
                self.start();
            });
            self.template = 'go_picking';
        },

        start: function(){
            var self = this;
            self.$elem = $(QWeb.render(this.template));
            $('#content').html(self.$elem);
            self.$modal = $('#modalWindow');
            self.add_listener_on_create_picking();
        },

        add_listener_on_create_picking: function(){
            var self = this;
            self.$elem.find('#create-wave').click(function(event){
                self.session.rpc('/picking_waves/create_picking', {
                }).then(function(data){
                    self.pickings = data.pickings;
                    self.current_picking = 0;

                    self.$elem = $(QWeb.render('picking_products', {
                            picking: data.pickings[self.current_picking],
                            'image': self.pickings[self.current_picking]['product'].product_image,

                    }));

                    $('#content').html(self.$elem);
                    self.current_barcode_needed = data.pickings[self.current_picking]['product'].ean13;
                    self.current_barcode_type = "product";
                });
            })

            // save the starting time, add the listener for barcode
            self.starting_time = new Date().getTime();
            self.add_listener_for_barcode();

        },
        add_listener_for_barcode: function(){
            var self = this;
            var pressed = false;
            var chars = [];
            $(document).off('keypress.barcode');
            $(document).on('keypress.barcode', function(e) {
                chars.push(String.fromCharCode(e.which));
                if (pressed == false) {
                    setTimeout(function(){
                        if (chars.length >= 6) {
                            var barcode = chars.join("");
                            self.process_barcode(barcode)
                        }
                        chars = [];
                        pressed = false;
                    },500);
                }
                pressed = true;
            });
        },
        process_barcode: function(barcode){
            var self = this;

            // check if the barcode scanned is the barcode we needed
            is_same_barcode = barcode.replace(/[\n\r]+/g, '')==self.current_barcode_needed;

            // hide the modal if we scanned another product/location with an open modal
            self.$modal.modal('hide');

            // Add the counter after the first scan and begin listening on it
            var $result = $(QWeb.render('counter',{}));
            $('#count').html($result);
            self.add_listener_on_quantity();

            if(self.current_barcode_type == "location"){
                // we need a location barcode
                if (is_same_barcode){
                    // if we got the needed barcode, go to the next picking
                    self.current_barcode_type = "product";
                    self.current_picking++;
                    self.current_barcode_needed = self.pickings[self.current_picking].product.ean13;

                    // validate the current move
                    self.session.rpc('/picking_waves/validate_move', {
                        'move_id': self.pickings[self.current_picking].move_id,
                    }).then(function(data){
                        // display the next product needed
                        self.$elem = $(QWeb.render('picking_products', {
                            picking: self.pickings[self.current_picking],
                            'image': self.pickings[self.current_picking]['product'].product_image,
                        }));
                        $('#content').html(self.$elem);

                        // should probably use this elsewhere :D
                        var msec = self.starting_time - new Date().getTime()
                        console.log("it took "+msec+" milliseconds to complete this picking")
                    });

                }else{
                    // if we didnt scan what we wanted, display an error message
                    var $result = $(QWeb.render('print_error_message',{
                        'type':'location',
                        'dest_location': self.pickings[self.current_picking].location_dest_name
                    }));
                    self.show_modal('Location Error', $result, false);
                }

            }else if(self.current_barcode_type == "product"){

                // we need a product barcode
                if (is_same_barcode){
                    //todo ICI plein de choses
                    if (parseInt($('#quantity input').val()) == self.pickings[self.current_picking].product.product_quantity){

                        // we have the correct amount of items
                        self.current_barcode_type = "location";
                        self.current_barcode_needed = self.pickings[self.current_picking].location_dest_barcode;

                    }else if (parseInt($('#quantity input').val()) > self.pickings[self.current_picking].product.product_quantity){

                        // we have TOO MUCH products!
                        var $result = $(QWeb.render('counter_error',{
                            'real': parseInt($('#quantity input').val()),
                            'expected': self.pickings[self.current_picking].product.product_quantity
                        }));

                        self.show_modal('Counter error', $result, false);
                    }

                }else{
                    // display an error message if we didnt scan the correct label
                    var $result = $(QWeb.render('print_error_message',{
                        'type':'product',
                        'image': self.pickings[self.current_picking]['product'].product_image,
                        'location': self.pickings[self.current_picking].location_name
                    }));
                    self.show_modal('Product Error', $result, false);
                }
            }

        },
        show_modal: function(title, content, block_modal){
            var self = this;
            if (typeof(block_modal)==='undefined') block_modal = true;
            self.$modal.find('.modal-title').html(title);
            self.$modal.find('.modal-body').html(content);
            if(block_modal){
                self.$modal.modal({
                    backdrop: 'static', // prevent from closing when clicking beside the modal
                    keyboard: false  // prevent closing when clicking on "escape"
                });
            }else{
                self.$modal.modal();
            }
        },
        add_listener_on_closing_modal: function(){
            var self = this;
            self.$modal.off('hide.bs.modal');
            self.$modal.on('hide.bs.modal', function() {
                self.$modal.find('.modal-title').empty();
                self.$modal.find('.modal-body').empty();
            })
        },
        add_listener_on_quantity: function(){
            var self = this;
            self.$elem.find('#quantity button').click(function(event){
                qty = parseInt($('#quantity input').val());

                if($(event.currentTarget).attr('data-dir') == 'up'){
                    qty++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 1){
                        qty--;
                    }
                }
                $('#quantity input').val(qty);
                $(':focus').blur()
            });
        },
    });
    instance.picking_waves.picking_selector = new picking_selector();
})();
