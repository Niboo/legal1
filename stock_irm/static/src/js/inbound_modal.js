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

    
    var purchase_order_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            this._super(caller);
            self.block_modal = true;
            self.body_template = 'supplier_purchase_orders';
            self.footer_template = 'confirm_purchase_orders';
            self.title = 'Select the impacted purchases orders';
            self.selected_purchases = [];
        },
        start: function (orders) {
            var self = this;
            self.$body = $(QWeb.render(self.body_template, {
                purchase_orders: orders
            }));
            self.$footer = $(QWeb.render(self.footer_template));
            this._super();
            self.add_listener_on_purchase();
            self.add_listener_on_purchase_footer();
        },
        add_listener_on_purchase: function(){
            var self = this;
            self.$modal.find('.purchase-btn').click(function(event){
                var purchase_id = parseInt($(event.currentTarget).attr('purchase-id'));
                var index = self.selected_purchases.indexOf(purchase_id);

                if(index != -1){
                    // If the PO is already in the list, we remove it from the list
                    self.selected_purchases.splice(index, 1);
                    $(event.currentTarget).removeClass('selected-purchase-btn');
                }else{
                    self.selected_purchases.push(purchase_id);
                    $(event.currentTarget).addClass('selected-purchase-btn');
                }
                if(self.selected_purchases.length > 0){
                    self.$modal.find('#no_purchases').hide();
                    self.$modal.find('#select_purchases').show();
                }else{
                    self.$modal.find('#select_purchases').hide();
                    self.$modal.find('#no_purchases').show();
                }
            });
        },
        add_listener_on_purchase_footer: function(){
            var self = this;
            self.$modal.find('.btn-success').off('click.select_purchases');
            self.$modal.find('.btn-success').off('click.no_purchases');

            self.$modal.find('#select_purchases').on('click.select_purchases', function (event) {
                self.caller.get_purchase_order_move_lines(self.selected_purchases);
                self.$modal.modal('hide');
            });
            self.$modal.find('#no_purchases').on('click.no_purchases', function (event) {
                self.caller.get_purchase_order_move_lines(self.selected_purchases);
                self.$modal.modal('hide');
            });
        },
    });

    instance.stock_irm.modal.purchase_order_modal = purchase_order_modal;

    var not_enough_label_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            this._super(caller);
            self.body_template = 'print_error_message';
            self.title = 'Not enough label printed';
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.body_template));
            this._super();
            self.add_listener_on_modal_print_button();
        },
        add_listener_on_modal_print_button: function(){
            var self = this;

            self.$modal.find('#modal_print_button').click(function(event){
                event.preventDefault();
                self.caller.print_missing_labels();
                self.$modal.modal('hide');

            })
        },
    });

    instance.stock_irm.modal.not_enough_label_modal = not_enough_label_modal;

    var box_barcode_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller, move_line, callback) {
            var self = this;
            this._super(caller);
            self.body_template = 'box_barcode_modal';
            self.footer_template = 'box_barcode_footer_modal';
            self.title = 'Scan the box barcode';
            self.block_modal = true;
            self.move_line = move_line;
            self.callback = callback
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.body_template));
            self.$footer = $(QWeb.render(self.footer_template));
            this._super();
            self.add_listener_on_barcode_modal_confirm();

            $(self.$modal).on('shown.bs.modal', function (e) {
                self.$modal.find('#box_barcode').focus();
                self.$modal.on();
            });
        },
        confirm_box: function(){
            var self = this;
            var barcode = self.$modal.find('#box_barcode').val();
            if(barcode){
                if(self.caller.is_box_free(barcode, self.move_line)){
                    self.session.rpc('/inbound_screen/check_package_empty', {
                        package_barcode: barcode
                    }).then(function(data){
                        if(data.status=="ok"){                        
                            $(self.$modal).on('hidden.bs.modal', function (e) {
                                self.caller.set_box(barcode, self.move_line, self.callback);
                                $(self.$modal).off();
                            });                        
                            self.$modal.modal('hide');
                        }else{
                            var error_modal = new instance.stock_irm.modal.box_already_used(self.caller, self.move_line, self.callback, "This box is already used elsewhere");
                            error_modal.start();
                        }
                    })
                } else {
                    var error_modal = new instance.stock_irm.modal.box_already_used(self.caller, self.move_line, self.callback, "This box is already used elsewhere");
                    error_modal.start();
                }
            }
        },
        add_listener_on_barcode_modal_confirm: function(){
            var self = this;
            self.$modal.find('#confirm_box_barcode').off('click.box.barcode');
            $('#box_barcode').keyup(function(event){
                if(event.keyCode==13){
                    self.confirm_box();
                }
            });
            self.$modal.find('#confirm_box_barcode').on('click.box.barcode', function(event){
                self.confirm_box();
            });
        },
    });

    instance.stock_irm.modal.box_barcode_modal = box_barcode_modal;

    var box_already_used = instance.stock_irm.modal.widget.extend({
        init: function (caller, move_line, callback, message) {
            var self = this;
            this._super(caller);
            self.title = 'Box already used';
            self.block_modal = true;
            self.footer_template = 'select_another_box_footer_modal';
            self.message = message;
            self.move_line = move_line;
            self.callback = callback;
        },
        start: function () {
            var self = this;
            self.$footer = $(QWeb.render(self.footer_template));
            self.$body = "<i class='fa fa-times fa-10x' style='color:red'></i><b style='font-size: 2em'>"+self.message+"</b>";
            this._super();
            self.add_listener_on_select_another();
        },
        add_listener_on_select_another: function(){
            var self = this;
            self.$modal.find('#select_another').off('click.another');
            self.$modal.find('#select_another').on('click.another', function(event){
                var modal = new instance.stock_irm.modal.box_barcode_modal(self.caller, self.move_line, self.callback);
                modal.start();
            });
        },
    });

    instance.stock_irm.modal.box_already_used = box_already_used;

    var confirmed_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Picking Confirmed!';
            self.block_modal = true;
        },
        start: function () {
            var self = this;
            self.$body = "<i class='fa fa-check fa-10x' style='color:green'></i><b style='font-size: 2em'>Wait for redirection...</b>";
            this._super();
        },
    });

    instance.stock_irm.modal.confirmed_modal = confirmed_modal;

    var back_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            this._super();
            var self = this;
            self.footer_template = 'go_back';
            self.title = 'Are you sure you want to go back?';
        },
        start: function () {
            var self = this;
            self.$body = 'All your changes will be cancelled.';
            self.$footer = $(QWeb.render(self.footer_template));
            this._super();
            self.add_listener_on_goback_button();
            self.add_listener_on_continue_button();
        },
        add_listener_on_goback_button: function(){
            var self = this;
            self.$modal.find('#close').click(function(event){
                self.$modal.modal('hide');
                window.location.href = "/inbound_screen";
            })
        },
        add_listener_on_continue_button: function(){
            var self = this;
            self.$modal.find('#continue_picking').click(function(event){
                self.$modal.modal('hide');
            })
        },
    });

    instance.stock_irm.modal.back_modal = back_modal;

    var going_back_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Confirm Going Back?';
            self.block_modal = true;
            self.template = 'going_back_modal';
            self.footer_template = 'going_back_modal_footer';
        },
        start: function (caller, qty, product_image) {
            var self = this;
            self.$body = $(QWeb.render(self.template, {
                image: product_image,
                quantity: qty,
            }));
            self.$footer = $(QWeb.render(self.footer_template));
            self.caller = caller;

            self._super();
            self.add_listener_on_cancel_button();
            self.add_listener_on_confirm_going_back_button();
        },
        add_listener_on_cancel_button: function(){
            var self = this;
            self.$modal.find('#continue').click(function(event){
                self.$modal.modal('hide');
                self.caller.add_listener_for_barcode();
            })
        },
        add_listener_on_confirm_going_back_button: function(){
            var self = this;
            self.$modal.find('#go_back').click(function(event){
                self.$modal.modal('hide');
                self.caller.destroy();
                self.caller.parent.refresh();
            })
        },
    });

    instance.stock_irm.modal.going_back_modal = going_back_modal;

    var confirm_move_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller, supplier_id, uncomplete_and_unexpected_move_line) {
            var self = this;
            this._super();
            self.title = 'Confirm unexpected or uncomplete Moves';
            self.block_modal = true;
            self.template = 'confirm_unexpected_uncomplete_move';
            self.footer_template = 'confirm_unexpected_uncomplete_move_footer';
            self.uncomplete_and_unexpected_move_line = uncomplete_and_unexpected_move_line;
            self.staging_id = $('#change-worklocation').attr('data-staging-id');
            self.supplier_id = supplier_id;
            self.caller = caller;
            self.packing_order_id = $('#packing-order-ref').attr('data-id');
        },
        start: function () {
            var self = this;
            self.session.rpc('/inbound_screen/get_incomplete_reason').then(function(data){
                if(data.status == 'ok'){
                    self.$body = $(QWeb.render(self.template, {
                        reasons: data.reasons,
                        moves : self.uncomplete_and_unexpected_move_line
                    }));
                    self.$footer = $(QWeb.render(self.footer_template));

                    self.show_modal();
                    self.add_listener_on_validate();
                    self.add_listener_on_finish();
                }
            });
        },
        add_listener_on_validate: function(){
            var self = this;
            self.$modal.find('.validate').click(function(event){
                var $button = $(event.currentTarget);
                var id = $button.attr('id');
                var reason_id = $button.parents('tr').find('select').val();

                var move = self.uncomplete_and_unexpected_move_line[id];
                if(move.is_new){
                    self.confirm_unexpected_move($button, move, reason_id);
                } else {
                    self.confirm_incomplete_move($button, move, reason_id);
                }
            });
        },
        add_listener_on_destinations: function($destinations, move){
            var self = this;
            console.log($destinations);
            $destinations.change(function(event){
                var destination_id = $(event.currentTarget).val();
                if(destination_id != 0){
                    $destinations.attr('disabled', 'disabled');
                    self.session.rpc('/inbound_screen/move_to_destination', {
                        box_name: move.box,
                        destination_id: destination_id,
                    }).then(function(data){
                        if(data.status == 'ok'){
                            move.state = 'done';
                            self.validate_line($destinations, data.destination);
                        } else {
                            $destinations.removeAttr('disabled');
                        }
                    });
                }
            })
        },
        validate_line: function($destinations, destination){
            var self = this;
            var moves_pending = _.filter(self.uncomplete_and_unexpected_move_line, function(move){
                return move.state === undefined || move.state != 'done';
            });
            if(moves_pending.length == 0){
                self.$modal.find('#finish').removeClass('hidden');
            }
            $destinations.parents('tr').addClass('bg-success');
            $destinations.replaceWith('<span style="font-size:1.4em" class="label pull-right label-primary">' + destination + '</span>');
        },
        confirm_incomplete_move: function($button, move, reason_id){
            var self = this;
            self.session.rpc('/inbound_screen/process_picking_line', {
                qty: move.quantity_already_scanned,
                picking_line_id: move.id,
                box_name: move.box,
                packing_order_id: self.packing_order_id,
                reason_id: reason_id,
            }).then(function(data){
                if (data.status != 'ok'){
                    var modal = new instance.stock_irm.modal.exception_modal();
                    modal.start(data.error, data.message);
                } else {
                    var $destinations = $(QWeb.render('confirm_unexpected_uncomplete_move_destinations', {
                        destinations: data.destinations
                    }));
                    $button.replaceWith($destinations);
                    self.add_listener_on_destinations($destinations, move);
                }
            });
        },
        confirm_unexpected_move: function($button, move, reason_id){
            var self = this;
            self.session.rpc('/inbound_screen/create_picking_for_unordered_lines', {
                extra_line: move,
                dest_box_id: self.staging_id,
                supplier_id: self.supplier_id,
                box_name: move.box,
                packing_order_id: self.packing_order_id,
                reason_id: reason_id
            }).then(function (data) {
                if (data.status != 'ok') {
                    var modal = new instance.stock_irm.modal.exception_modal();
                    modal.start(data.error, data.message);
                } else {
                    var $destinations = $(QWeb.render('confirm_unexpected_uncomplete_move_destinations', {
                        destinations: data.destinations
                    }));
                    $button.replaceWith($destinations);
                    self.add_listener_on_destinations($destinations, move);
                }
            });
        },
        add_listener_on_finish: function(){
            var self = this;
            self.$modal.find('#finish').click(function(event){
                var modal = new instance.stock_irm.modal.confirm_note_modal(self.caller);
                modal.start();
            });
        },
    });

    instance.stock_irm.modal.confirm_move_modal = confirm_move_modal;

    var confirm_note_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            this._super();
            self.title = 'Confirm Inbound Picking';
            self.block_modal = true;
            self.template = 'packing_order_note';
            self.footer_template = 'packing_order_note_footer';
            self.caller = caller;
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.template));
            self.$footer = $(QWeb.render(self.footer_template));

            self._super();
            self.add_listener_on_confirm_note();
        },
        add_listener_on_confirm_note: function(){
            var self = this;
            self.$modal.find('#confirm_note').click(function(event){
                var note = self.$modal.find('#packing_note').val();
                self.caller.confirm(note);
            })
        },
    });

    instance.stock_irm.modal.confirm_note_modal = confirm_note_modal;

    var close_box_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Close Current Box';
            self.block_modal = false;
            self.template = 'propose_close_box';
            self.footer_template = 'propose_close_box_footer';
        },
        start: function (caller, box_barcode) {
            var self = this;
            self.$body = $(QWeb.render(self.template));
            self.$footer = $(QWeb.render(self.footer_template));
            self.box_barcode = box_barcode;
            self.caller = caller;

            self._super();
            self.add_listener_on_close_box();
            self.add_listener_on_cancel();
        },
        add_listener_on_cancel: function(){
            var self = this;

            self.$modal.find('#cancel').off('click.confirm_bote');
            self.$modal.find('#cancel').on('click.confirm_bote', function (event) {
                    self.$modal.modal('hide');
            });
        },
        add_listener_on_close_box: function(){
            var self = this;

            self.$modal.find('#close').off('click.close');
            self.$modal.find('#close').on('click.close', function (event) {
                self.caller.close_box(self.box_barcode)
                self.$modal.modal('hide');
            });

        },
    });

    instance.stock_irm.modal.close_box_modal = close_box_modal;


    var validate_po_line_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Validate Move';
            self.block_modal = true;
            self.template = 'valide_po_line';
            self.footer_template = 'validate_po_line_footer';
            self.packing_order_id = $('#packing-order-ref').attr('data-id');
        },
        start: function (caller, nb_product_more, move_line, product) {
            var self = this;
            self.nb_product_more = nb_product_more;
            self.$body = $(QWeb.render(self.template,{
                nb_product_more: nb_product_more
            }));

            self.$footer = $(QWeb.render(self.footer_template,{
                nb_product_more: nb_product_more
            }));
            self.caller = caller;
            self.move_line = move_line;
            self.product = product;
            self._super();
            self.add_listener_on_validate();
            self.add_listener_on_cancel();
        },
        add_listener_on_cancel: function(){
            var self = this;

            self.$modal.find('#cancel').off('click.close');
            self.$modal.find('#cancel').on('click.close', function (event) {
                self.caller.destroy();
                self.caller.parent.start();
                self.$modal.modal('hide');
            });
        },
        add_listener_on_validate: function(){
            var self = this;
            self.$modal.find('#validate').off('click.validate');
            self.$modal.find('#validate').on('click.validate', function (event) {
                self.session.rpc('/inbound_screen/process_picking_line', {
                    qty: self.move_line.quantity_already_scanned,
                    picking_line_id: self.move_line.id,
                    box_name: self.move_line.box,
                    packing_order_id: self.packing_order_id,
                }).then(function(data){
                    if (data.status == 'ok'){
                        var modal = new instance.stock_irm.modal.select_next_destination_modal();
                        modal.start(self.caller, data.destinations, self.nb_product_more, self.move_line, self.product);
                    }
                });
            })
        },
    });

    instance.stock_irm.modal.validate_po_line_modal = validate_po_line_modal;

    var select_next_destination_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Destination of this package';
            self.template = 'select_next_destination';
            self.block_modal = true;
        },
        start: function (caller, destinations, leftover, move_line, product) {
            var self = this;
            self.$body = $(QWeb.render(self.template, {
                destinations: destinations
            }));
            self.caller = caller;
            self.leftover = leftover;
            self.move_line = move_line;
            self.product = product;

            self._super();
            self.add_listener_on_destinations(move_line);
        },
        add_listener_on_destinations: function(move){
            var self = this;

            self.$modal.find('.destination').off('click.destination');
            self.$modal.find('.destination').on('click.destination', function (event) {
                var destination_id = $(event.currentTarget).attr('data-id');
                if(destination_id != 0){
                    self.session.rpc('/inbound_screen/move_to_destination', {
                        box_name: move.box,
                        destination_id: destination_id,
                    }).then(function(data){
                        if(data.status == 'ok') {
                            if (self.leftover == 0) {
                                self.$modal.modal('hide');
                                self.caller.destroy();
                                self.caller.start();
                            } else {
                                self.caller.get_the_box(self.product, self);
                            }
                        }
                    });
                }
            })
        },
        do_after_set_box: function(box, move_line){
            var self = this;
            self.caller.add_product(self.product, self.leftover, move_line);
        },
    });

    instance.stock_irm.modal.select_next_destination_modal = select_next_destination_modal;


})();
