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
        start: function() {
            var self = this;
            self._super();
            self.allow_scan_package = true;
            self.selected_package_ids = [];
            self.product_scanned = false

            self.session.rpc('/outbound_wave/get_wave_template', {}).then(function (data) {
                if (data.status == "ok") {
                    var modal = new instance.stock_irm.modal.select_wave_template(self, data.wave_templates);
                    modal.start();
                    self.add_listener_for_barcode();
                }
            });
        },
        get_waves: function(wave_template){
            var self = this;

            self.wave_template = wave_template;

            self.qty_in_box = 0;
            self.first_pass = false;

            self.session.rpc('/outbound_wave/get_outbound_wave', {
                wave_template_id: self.wave_template.id
            }).then(function(data){
                if (data.status == 'ok'){
                    self.$elem = $(QWeb.render(self.template, {
                        waves: data.waves,
                    }));
                    $('#content').html(self.$elem);
                    self.add_listener_on_create_picking();
                    self.add_listener_on_manual_input()

                    self.$elem.find('.wave-div a').click(function(event){

                        var wave_id = $(event.currentTarget).attr('wave-id');
                        self.session.rpc('/outbound_wave/get_wave', {
                            'wave_id': wave_id,
                        }).then(function(data){
                            self.$nav.find('#back').show();
                            self.allow_scan_package = false;

                            if(data.status == "empty"){
                                self.$elem = $(QWeb.render('picking_empty', {}));
                                $('#content').html(self.$elem);
                            } else {
                                self.move_list = data.move_list;
                                self.current_move_index = 0;
                                self.pickings = data.picking_list;
                                self.wave_id = data.wave_id;
                                self.wave_name = data.wave_name;
                                self.select_cart();

                                // save the starting time, add the listener for barcode
                                self.starting_time = new Date().getTime();
                            }
                        });
                    })
                }
            });
        },
        add_listener_on_create_picking: function(){
            var self = this;
            self.$elem.find('#create-wave').click(function(event){

                self.session.rpc('/outbound_wave/create_picking', {
                    wave_template_id: self.wave_template.id,
                    selected_packages: self.selected_package_ids,
                }).then(function(data){
                    self.allow_scan_package = false;
                    self.$nav.find('#back').show();
                    self.add_listener_on_back_button();

                    if(data.status == "empty"){
                        self.$elem = $(QWeb.render('picking_empty', {}));
                        $('#content').html(self.$elem);
                    } else {

                        self.move_list = data.move_list;
                        self.current_move_index = 0;
                        self.pickings = data.picking_list;
                        self.wave_id = data.wave_id;
                        self.wave_name = data.wave_name;
                        self.select_cart();

                        // save the starting time, add the listener for barcode
                        self.starting_time = new Date().getTime();
                    }
                });
            })
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
        add_listener_on_goback_button: function(){
            var self = this;
            self.$modal.find('#close_wave').click(function(event){
                self.$modal.modal('hide');
                window.location.href = "/picking_waves";
            })
        },
        add_listener_on_continue_button: function(){
            var self = this;
            self.$modal.find('#continue_wave').click(function(event){
                self.$modal.modal('hide');
            })
        },
        display_page: function(){
            var self = this;
            self.set_current_picking_index();
            self.$elem = $(QWeb.render('picking_layout', {
                'wave_id': self.wave_id,
                'pickings': self.pickings,
                'product': self.move_list[self.current_move_index]['product'],
                'location_name': self.move_list[self.current_move_index].product.location_name,
                'moves': self.move_list.slice(
                    self.current_move_index + 1,
                    self.current_move_index + 6)
            }));
            $('#content').html(self.$elem);
            $('#wave-id').html(self.wave_name);
            $('#wave-id-li').show();
	        $('#print-wave').show();
            self.add_listener_on_manual_input();
            self.add_listener_on_skip_picking();
            self.add_listener_on_picking_list();
            var $message = $(QWeb.render('info_first_barcode'));
            $('#info_message').html($message)

            self.current_product_barcode = self.move_list[self.current_move_index]['product'].ean13;
            self.current_destination_barcode = self.pickings[self.current_picking_index].box_barcode;
        },
        add_listener_on_manual_input: function(){
            var self = this;
            $("#manual-barcode-input").off('click.manual');
            $("#manual-barcode-input").on('click.manual', function (event) {
                self.add_listener_on_numpad();
            });
        },
        add_listener_on_skip_picking: function(){

            var self = this;

            $("#skip-picking-line").off('click.skip');
            $("#skip-picking-line").on('click.skip', function (event) {
                self.current_move_index++;
                $("#current_product").animate({opacity: '0.4', backgroundColor: "red"}, 200);
                $('#current_product').hide("slide",{direction:'right', backgroundColor: "red"}, 400, function(){
                    if(self.current_move_index >= self.move_list.length){
                        // No more products
                        self.validate_wave();
                    }else{
                        self.display_page();
                    }
                });
            });
        },
        add_listener_on_numpad: function(){
            var self = this;
            $('.num-pad .circle').off('click.numpad');
            $('.num-pad .circle').on('click.numpad', function (event) {
                var $target = $(event.currentTarget);
                value = $target.find("span").text();
                if(value=="C"){
                   self.$elem.find('#manual-barcode').val("");
                }else if(value=="Enter"){
                    self.process_barcode(self.$elem.find('#manual-barcode').val());
                    self.$elem.find('#manual-barcode').val("");

                }else{
                    self.$elem.find('#manual-barcode').val(self.$elem.find('#manual-barcode').val()+value);
                }
                $(':focus').blur()

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
                    },100);
                }
                pressed = true;
            });
        },
        process_barcode: function(barcode){
            var self = this;
            barcode = barcode.replace(/[\s]*/g, '');

            if(self.allow_scan_package){
                self.add_package(barcode);
            }else{
                // check if the barcode scanned is the barcode we needed
                var is_product_barcode = barcode == self.current_product_barcode;
                var is_destination_barcode = barcode == self.current_destination_barcode;

                var qty = parseInt($('#quantity_wave input').val());
                var current_move = self.move_list[self.current_move_index];
                if(is_product_barcode){
                    qty++;
                    $('#info').show();
                    $('#quantity_wave input').val(qty);
                    self.add_listener_on_quantity();
                    self.add_listener_on_keyboard_quantity();
                    self.change_background_on_quantity(qty);
                    self.product_scanned = true;
                }else {
                    if(!self.product_scanned){
                        // display an error in case the product is not scanned...
                        var modal = new instance.stock_irm.modal.scan_product_modal();
                        modal.start()
                    }
                    // location may be scanned
                    var move_qty = current_move.product.product_quantity;
                    var sum = self.qty_in_box + qty;

                    if (sum < move_qty) {
                        // Update the quantity
                        var qty_to_take = move_qty - self.qty_in_box;
                        self.qty_in_box = sum;
                        self.$elem.find('#quantity_wave input').val(0);
                        self.$elem.find('#qty_in_box').text(self.qty_in_box);
                        self.$elem.find('#expected_qty').text(qty_to_take);
                    } else if (sum > move_qty) {
                        // Not the expected quantity, display an error modal
                        var modal = new instance.stock_irm.modal.wrong_quantity_modal();
                        modal.start(sum, move_qty)
                    } else {
                        if (is_destination_barcode) {
                            self.trigger_next_product(current_move);
                        } else {
                            self.session.rpc('/outbound_wave/check_package_empty', {
                                barcode: barcode
                            }).then(function (data) {
                                if (data.status == 'ok') {
                                    self.pickings[self.current_picking_index].box_barcode = barcode;
                                    self.trigger_next_product(current_move);
                                } else {
                                    var modal = new instance.stock_irm.modal.exception_modal();
                                    modal.start('Error', 'This box is already used for a different picking');
                                }
                            });
                        }
                    }
                }
            }
        },
        add_package: function(barcode){
            var self = this;

            self.session.rpc('/outbound_wave/get_package', {
                'package_barcode': barcode,
                'wave_template_id': self.wave_template.id,
            }).then(function(data){
                if(data.status=='ok'){
                    self.$elem.find('#unfinished_waves').hide();
                    self.$elem.find('#selected_packages').html('Selected Packages:');
                    self.$elem.find('#create-wave').html('<span>Create a picking wave including:</span>')
                    var $package = $(QWeb.render('begon_package', {
                        package:data
                    }));

                    if($.inArray(data.id, self.selected_package_ids) == -1){
                        self.selected_package_ids.push(data.id);
                        self.$elem.find('#packages-list').append($package);
                    }else{
                        var modal = new instance.stock_irm.modal.already_scanned_box();
                        modal.start();
                    }
                }else{
                    var modal = new instance.stock_irm.modal.package_not_found();
                    modal.start();
                }
            });
        },
        trigger_next_product: function(current_move){
            var self = this;
            // right location scanned, validate the move
            self.session.rpc('/picking_waves/validate_move', {
                move_id: current_move.move_id,
                cart_id: self.cart_id,
                box_barcode: self.pickings[self.current_picking_index].box_barcode,
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
            self.product_scanned = false;

            // HAPPY FLOW! Go to the next product
            self.current_move_index++;
            $("#current_product").animate({opacity: '0.4', backgroundColor: "green"}, 200);
            $('#current_product').hide("slide",{direction:'left', backgroundColor: "green"}, 400, function(){
                if(self.current_move_index >= self.move_list.length){
                    // No more products
                    self.validate_wave();
                }else{
                    self.current_product_barcode = self.move_list[self.current_move_index].product.ean13;
                    self.current_destination_barcode = self.move_list[self.current_move_index].location_dest_barcode;
                    self.display_page();
                }
            })
        },
        validate_wave: function(){
            var self = this;

            self.session.rpc('/outbound_wave/get_wave_time', {
                wave_id:self.wave_id,
            }).then(function (data) {
                if (data.status == "ok") {
                    var total_time = data.total_time
                    var modal = new instance.stock_irm.modal.end_wave_modal(self);
                    modal.start(total_time*60, self.pickings);
                }
            });

        },
        add_listener_on_quantity: function(){
            var self = this;
            var qty = parseInt($('#quantity_wave input').val());

            $('#quantity_wave button').off('click.quantity');
            $('#quantity_wave button').on('click.quantity', function (event) {
                var qty = parseInt($('#quantity_wave input').val());
                if($(event.currentTarget).attr('data-dir') == 'up'){
                    qty++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 1){
                        qty--;
                    }
                }
                self.change_background_on_quantity(qty);
                self.$elem.find('#quantity_wave input').val(qty);
                $(':focus').blur()
            });
        },
        add_listener_on_keyboard_quantity: function(){
            var self = this;

            $('#quantity-input-value').keyup(function(event){
               var qty = parseInt($('#quantity_wave input').val());
                self.change_background_on_quantity(qty);
            })
        },
        change_background_on_quantity: function(qty){
            var self = this;
            var expected_qty = parseInt(self.$elem.find('#expected_qty').html());
            var current_product_div = document.getElementById( 'current_product' );

            if(qty == expected_qty) {
                current_product_div.style.backgroundColor = 'rgba(159,204,135,0.5)';
                var $message = $(QWeb.render('info_location_barcode'));
                $('#info_message').html($message)
            } else if(qty > expected_qty) {
                current_product_div.style.backgroundColor = 'rgba(255,148,148,0.5)';
                var $message = $(QWeb.render('info_too_much_barcode'));
                $('#info_message').html($message)
            } else {
                current_product_div.style.backgroundColor = 'rgba(255,255,255,1.0)';
                var $message = $(QWeb.render('info_more_barcode'));
                $('#info_message').html($message)
            };
        },
        add_listener_on_picking_list: function() {
            var self = this;
            
            self.$elem.find('#picking-list a').click(function(event){

                var picking_id = $(event.currentTarget).attr('data-id');
                current_picking = jQuery.grep(self.move_list, function( a ) {
                    return a.picking_id == picking_id;
                });

                var modal = new instance.stock_irm.modal.picking_modal(current_picking[0].picking_name);
                modal.start(current_picking);
            })
        },
	    add_listener_on_endbox: function(){
            var self = this;
            $('#content').find('.end-box').click(function(event){
                event.preventDefault();
                if($(event.currentTarget).hasClass("btn-warning")){
                    $(event.currentTarget).switchClass("btn-warning", "btn-success", 100)
                }else{
                    $(event.currentTarget).switchClass("btn-success", "btn-warning", 100)
                }
                $(':focus').blur();
            })
        },
        select_cart: function () {
            var self = this;
            self.session.rpc('/outbound_wave/get_carts', {
                wave_id: self.wave_id,
            }).then(function (data) {
                if(data.status == 'ok'){
                    var modal = new instance.stock_irm.modal.select_cart_modal();
                    modal.start(self, data.carts);
                } else {
                    var modal = new instance.stock_irm.modal.exception_modal();
                    if(data.status == 'empty'){
                        modal.start('Error', 'No cart found');
                    } else {
                        modal.start('Error', 'Could not retrieve the cart list');
                    }
                }
            });
        },
        set_current_picking_index: function () {
            var self = this;
            for(var i in self.pickings){
                if(self.pickings[i].picking_id == self.move_list[self.current_move_index].picking_id){
                    self.current_picking_index = i;
                }
            }
        }
    });
    instance.picking_waves.picking_selector = new picking_selector();
})();
