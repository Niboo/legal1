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
            self.qty_in_box = 0;
            self.first_pass = false;

            self.session.rpc('/picking_waves/get_picking', {})
            .then(function(data){
                if (data.status == 'ok'){
                    self.$elem = $(QWeb.render(self.template, {
                        waves: data.waves,
                    }));
                    $('#content').html(self.$elem);
                    self.add_listener_on_create_picking();
                }
            });
        },
        add_listener_on_create_picking: function(){
            var self = this;
            self.$elem.find('#create-wave').click(function(event){
                self.session.rpc('/picking_waves/create_picking', {})
                        .then(function(data){
                    if(data.status == "empty"){
                        self.$elem = $(QWeb.render('picking_empty', {}));
                        $('#content').html(self.$elem);
                    } else {
                        self.move_list = data.move_list;
                        self.current_move_index = 0;
                        self.pickings = data.picking_list;
                        self.wave_id = data.wave_id;
                        self.display_page();

                        // save the starting time, add the listener for barcode
                        self.starting_time = new Date().getTime();
                        self.add_listener_for_barcode();
                    }
                });
            })
        },
        display_page: function(){
            var self = this;

            self.$elem = $(QWeb.render('picking_layout', {
                'wave_id': self.wave_id,
                'pickings': self.pickings,
                'product': self.move_list[self.current_move_index]['product'],
                'location_dest_name': self.move_list[self.current_move_index].location_dest_name,
                'moves': self.move_list.slice(
                    self.current_move_index + 1,
                    self.current_move_index + 6)
            }));
            $('#content').html(self.$elem);
            self.add_listener_on_manual_input();
            self.current_product_barcode = self.move_list[self.current_move_index]['product'].ean13;
            self.current_destination_barcode = self.move_list[self.current_move_index].location_dest_barcode;
        },
        add_listener_on_manual_input: function(){
            var self = this;
            $("#manual-barcode-input").off('click.manual');
            $("#manual-barcode-input").on('click.manual', function (event) {
                self.add_listener_on_numpad();
            });
        },
        add_listener_on_numpad: function(){
            var self = this;
            $('.num-pad .circle').off('click.numpad');
            $('.num-pad .circle').on('click.numpad', function (event) {
                var $target = $(event.currentTarget);
                value = $target.find("span").text()
                if(value=="C"){
                   self.$elem.find('#manual-barcode').val("");
                }else if(value=="Enter"){
                      self.process_barcode(self.$elem.find('#manual-barcode').val());
                }else{
                    self.$elem.find('#manual-barcode').val(self.$elem.find('#manual-barcode').val()+value);
                    self.$elem.find('#manual-barcode').val("");
                }
            });
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
            var is_product_barcode = barcode.replace(/[\n\r]+/g, '') == self.current_product_barcode;
            var is_destination_barcode = barcode.replace(/[\n\r]+/g, '') == self.current_destination_barcode;

            var qty = parseInt($('#quantity_wave input').val());
            var current_move = self.move_list[self.current_move_index]

            if(is_product_barcode){
                qty++
                $('#info').show();
                $('#quantity_wave input').val(qty);
                self.add_listener_on_quantity();

            }else if(is_destination_barcode){
                // location scanned
                var move_qty = current_move.product.product_quantity
                var sum = self.qty_in_box + qty;

                if(sum == move_qty){
                    self.trigger_next_product(current_move);
                }else if(sum < move_qty){
                    // Update the quantity
                    var qty_to_take = move_qty - self.qty_in_box;
                    self.qty_in_box = sum;
                    self.$elem.find('#quantity_wave input').val(0);
                    self.$elem.find('#qty_in_box').text(self.qty_in_box);
                    self.$elem.find('#expected_qty').text(qty_to_take);
                } else {
                    // Not the expected quantity, display an error modal
                    var $result = $(QWeb.render('counter_error',{
                        'real': sum,
                        'expected': move_qty
                    }));
                    self.show_modal('Item Count Error', $result, "", false);
                }
            }else{
                if(qty == 0){
                    var $result = $(QWeb.render('print_error_message',{
                        'type':'product',
                        'image': current_move.product.product_image,
                        'location': current_move.product.location_name
                    }));
                    self.show_modal('Product Error', $result, "", false);
                }else if(qty == current_move.product.product_quantity){
                    // good number of product, but not good location
                    var $result = $(QWeb.render('print_error_message',{
                        'type':'location',
                        'dest_location': current_move.location_dest_name
                    }));
                    self.show_modal('Location Error', $result, "", false);
                }else{
                    // More product expected, but something else scanned
                    var $result = $(QWeb.render('counter_error',{
                        'real': qty,
                        'expected': current_move.product.product_quantity
                    }));
                    self.show_modal('Item Count Error', $result, "", false);
                }
            }
        },
        trigger_next_product: function(current_move){
            var self = this;
            // right location scanned, validate the move
            self.session.rpc('/picking_waves/validate_move', {
                'move_id': current_move.move_id,
            }).then(function(data){
                var index = $.map(self.pickings, function(obj, index) {
                    if(obj.picking_id == data.picking_id) {
                        return index;
                    }
                })
                self.pickings[index].progress_done = data.progress_done
                $("#"+data.picking_id).css({"width":data.progress_done+'%'});
                self.qty_in_box = 0;
            });

            // HAPPY FLOW! Go to the next product
            self.current_move_index++;

            if(self.current_move_index >= self.move_list.length){
                // No more products
                self.validate_wave();
            }else{
                self.current_product_barcode = self.move_list[self.current_move_index].product.ean13;
                self.current_destination_barcode = self.move_list[self.current_move_index].location_dest_barcode;
                self.display_page();
            }
        },
        validate_wave: function(){
            var self = this;
            var msec = new Date().getTime() - self.starting_time;

            self.session.rpc('/picking_waves/validate_wave', {
                'wave_id': self.wave_id,
                'time_to_complete': msec,
            }).then(function(data){
                if (data.status == 'ok'){
                    self.show_modal('Wave Finished!', "<i class='fa fa-check fa-10x' style='color:green'></i><b style='font-size: 2em'>Wait for redirection...</b>");
                    window.setTimeout(function(){
                        window.location.href = "/picking_waves";
                    }, 3000);
                }
            });
        },
        add_listener_on_quantity: function(){
            var self = this;
            var qty = parseInt($('#quantity_wave input').val());

            $('#quantity_wave button').off('click.quantity');
            $('#quantity_wave button').on('click.quantity', function (event) {
                if($(event.currentTarget).attr('data-dir') == 'up'){
                    qty++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 1){
                        qty--;
                    }
                }
                self.$elem.find('#quantity_wave input').val(qty);
                $(':focus').blur()
            });
        },
    });
    instance.picking_waves.picking_selector = new picking_selector();
})();
