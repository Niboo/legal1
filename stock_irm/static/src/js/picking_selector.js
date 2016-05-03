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
            self.first_pass = false;
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
                    if(data.status == "empty"){
                        self.$elem = $(QWeb.render('picking_empty', {
                        }));
                        $('#content').html(self.$elem);                    }
                    else{
                        self.move_list = data.move_list;
                        self.current_move = 0;
                        self.pickings = data.picking_list
                        self.$elem = $(QWeb.render('picking_layout', {
                            'wave_id': data.wave_id,
                        }));
                        $('#content').html(self.$elem);
                        self.display_page();
                    }
                });
            })

            // save the starting time, add the listener for barcode
            self.starting_time = new Date().getTime();
            self.add_listener_for_barcode();

        },
        display_page: function(){
            var self = this;

            if(!self.first_pass){
                var $picking_list = $(QWeb.render('picking_list',{
                    'pickings': self.pickings,
                }));
            }
            self.first_pass = true;
            self.$elem.find("#picking_list").html($picking_list);

            // generate the current product
            var $current_produt = $(QWeb.render('current_product',{
                'product': self.move_list[self.current_move]['product'],
                'location_dest_name' : self.move_list[self.current_move].location_dest_name
            }));
            self.$elem.find("#current_product").html($current_produt);

            var $next_products = $(QWeb.render('next_products',{
                // retrieve the next 5 products to display them
                'moves': self.move_list.slice(self.current_move+1,self.current_move+6)
            }));
            self.$elem.find("#next_products").html($next_products);

            self.current_product_barcode = self.move_list[self.current_move]['product'].ean13;
            self.current_destination_barcode = self.move_list[self.current_move].location_dest_barcode
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

            // hide the modal if we scanned another product/location with an open modal
            self.$modal.modal('hide');

            // check if the barcode scanned is the barcode we needed
            is_product_barcode = barcode.replace(/[\n\r]+/g, '')==self.current_product_barcode;
            is_destination_barcode = barcode.replace(/[\n\r]+/g, '')==self.current_destination_barcode;

            qty = parseInt($('#quantity_wave input').val());

            if(is_product_barcode){
                console.log("it is the barcode product");
                qty++
                $('#info').show();
                $('#quantity_wave input').val(qty);
                self.add_listener_on_quantity();

            }else if(is_destination_barcode){
                // location scanned
                console.log("it is the destination barcode");

                if(qty == self.move_list[self.current_move].product.product_quantity){
                    // right location scanned, validate the move
                    self.session.rpc('/picking_waves/validate_move', {
                        'move_id': self.move_list[self.current_move].move_id,
                    }).then(function(data){
                        index = $.map(self.pickings, function(obj, index) {
                            if(obj.picking_id == data.picking_id) {
                                return index;
                            }
                        })

                        self.pickings[index].progress_done = data.progress_done
                        $("#"+data.picking_id).css({"width":data.progress_done+'%'});
                    });

                    // HAPPY FLOW! Go to the next product
                    self.current_move++;

                    if(self.current_move >= self.move_list.length){
                        //Then we have finished the scanning!
                        var msec = self.starting_time - new Date().getTime()
                        console.log("it took "+msec+" milliseconds to complete this picking")
                    }else{
                        self.current_product_barcode = self.move_list[self.current_move].product.ean13;
                        self.current_destination_barcode = self.move_list[self.current_move].location_dest_barcode;
                        self.display_page();
                    }

                }else{
                    // Not the expected quantity, display an error modal
                    var $result = $(QWeb.render('counter_error',{
                        'real': qty,
                        'expected': self.move_list[self.current_move].product.product_quantity
                    }));
                    self.show_modal('Item Count Error', $result, "", false);
                }
            }else{
                if(qty == 0){
                    var $result = $(QWeb.render('print_error_message',{
                        'type':'product',
                        'image': self.move_list[self.current_move].product.product_image,
                        'location': self.move_list[self.current_move].product.location_name
                    }));
                    self.show_modal('Product Error', $result, "", false);
                }else if(qty == self.move_list[self.current_move].product.product_quantity){
                    // good number of product, but not good location
                    var $result = $(QWeb.render('print_error_message',{
                        'type':'location',
                        'dest_location': self.move_list[self.current_move].location_dest_name
                    }));
                    self.show_modal('Location Error', $result, "", false);
                }else{
                    // More product expected, but something else scanned
                    var $result = $(QWeb.render('counter_error',{
                        'real': qty,
                        'expected': self.move_list[self.current_move].product.product_quantity
                    }));
                    self.show_modal('Item Count Error', $result, "", false);
                }
            }
        },
        show_modal: function(title, content, footer, block_modal){
            var self = this;
            if (typeof(footer)==='undefined') footer = '';
            if (typeof(block_modal)==='undefined') block_modal = true;

            if (block_modal){
                self.$modal = $('#blockedModalWindow');
            }else{
                self.$modal = $('#modalWindow');
            }
            $(document).off('keypress.barcode');
            self.$modal.find('.modal-title').html(title);
            self.$modal.find('.modal-body').html(content);
            self.$modal.find('.modal-footer').html(footer);
            if(block_modal){
                self.$modal.modal({
                    backdrop: 'static', // prevent from closing when clicking beside the modal
                    keyboard: false  // prevent closing when clicking on "escape"
                });
            }else{
                self.$modal.modal();
            }
            self.$modal.on('hidden.bs.modal', function () {
                $(document).off('keypress.barcodeuser');
                self.add_listeners();
            });
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
            qty = parseInt($('#quantity_wave input').val());

            $('#quantity_wave button').off('click.quantity');
            $('#quantity_wave button').on('click.quantity', function (event) {
                if($(event.currentTarget).attr('data-dir') == 'up'){
                    qty++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 1){
                        qty--;
                    }
                }
                $('#quantity_wave input').val(qty);
                $(':focus').blur()
            });
            if(qty == self.move_list[self.current_move].product.product_quantity){
                $('#info').show();
            }else{
                $('#info').hide();
            }
        },
    });
    instance.picking_waves.picking_selector = new picking_selector();
})();
