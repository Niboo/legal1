///////////////////////////////////////////////////////////////////////////////
//
//    Author: Pierre Faniel
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

    var crm_claim_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            this._super(caller);
            self.block_modal = true;
            self.body_template = 'customer_crm_claims';
            self.footer_template = 'confirm_crm_claims';
            self.title = 'Select the impacted claims';
            self.selected_claims = [];
        },
        start: function (claims) {
            var self = this;
            self.$body = $(QWeb.render(self.body_template, {
                claims: claims
            }));
            self.$footer = $(QWeb.render(self.footer_template));
            this._super();
            self.add_listener_on_claim();
            self.add_listener_on_claim_footer();
        },
        add_listener_on_claim: function () {
            var self = this;
            self.$modal.find('.claim-btn').click(function (e) {
                var $this = $(this);
                var claim_id = parseInt($this.attr('claim-id'));
                var index = self.selected_claims.indexOf(claim_id);

                if (index != -1) {
                    // If the PO is already in the list, we remove it from the list
                    self.selected_claims.splice(index, 1);
                    $this.removeClass('selected-claim-btn');
                } else {
                    self.selected_claims.push(claim_id);
                    $this.addClass('selected-claim-btn');
                }
                self.$modal.find('#select_claims').toggle(self.selected_claims.length > 0);
            });
        },
        add_listener_on_claim_footer: function () {
            var self = this;
            self.$modal.find('.btn-success').off('click.select_claims');

            self.$modal.on('click.select_claims', '#select_claims', function (e) {
                self.$modal.modal('hide');
                self.$modal.on('hidden.bs.modal', function () {
                    self.caller.get_claim_move_lines(self.selected_claims);
                    self.$modal.off();
                })
            });
        },
    });

    instance.stock_irm.modal.crm_claim_modal = crm_claim_modal;

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
                window.location.href = "/rma_screen";
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



    var select_cart_modal = instance.stock_irm.modal.widget.extend({
        template: 'cart_result_body',
        init: function (block_modal) {
            var self = this;
            this._super();
            self.title = 'Select a cart';
            self.block_modal = block_modal;
        },
        start: function (caller, carts) {
            var self = this;
            self.caller = caller;
            self.carts = carts;
            self.$body = $(QWeb.render(self.template, {
                carts: carts,
                current_cart: self.caller.cart,
            }));
            self.footer_template = 'generic_confirm_button';
            self._super();
            self.add_listener_on_cart_button();
        },
        add_listener_on_cart_button: function () {
            var self = this;
            self.$body.find('.cart').off('click');
            self.$body.find('.cart').on('click', function (e) {
                var $this = $(this);
                var cart = {
                    id: parseInt($this.attr('cart-id')),
                    name: $this.attr('cart-name'),
                };
                self.$modal.modal('hide');
                self.$modal.on('hidden.bs.modal', function () {
                    self.caller.set_cart(cart);
                    self.$modal.off();
                    self.caller.add_listener_for_barcode();
                });
            })
        }
    });

    instance.stock_irm.modal.select_cart_modal = select_cart_modal;

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
        start: function (show_cancel) {
            var self = this;
            // set to false if no parameter given
            if (show_cancel !== true) {
                show_cancel = false;
            }
            self.$body = $(QWeb.render(self.body_template));
            self.$footer = $(QWeb.render(self.footer_template,{
                'show_cancel': show_cancel,
            }));

            this._super();
            self.add_listener_on_barcode_modal_confirm(show_cancel);
            if (show_cancel == true) {
                self.add_listener_on_cancel();
            }
            $(self.$modal).on('shown.bs.modal', function (e) {
                self.$modal.find('#box_barcode').focus();
                self.$modal.on();
            });
        },
        confirm_box: function(show_cancel){
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
                            error_modal.start(show_cancel);
                        }
                    }, function(data){
                        self.request_error(data);
                    });
                } else {
                    var error_modal = new instance.stock_irm.modal.box_already_used(self.caller, self.move_line, self.callback, "This box is already used elsewhere");
                    error_modal.start(show_cancel);
                }
            }
        },
        add_listener_on_barcode_modal_confirm: function(show_cancel){
            var self = this;
            self.$modal.find('#confirm_box_barcode').off('click.box.barcode');
            $('#box_barcode').keyup(function(event){
                if(event.keyCode==13){
                    self.confirm_box(show_cancel);
                }
            });
            self.$modal.find('#confirm_box_barcode').on('click.box.barcode', function(event){
                self.confirm_box(show_cancel);
            });
        },
        add_listener_on_cancel: function(){
            var self = this;
            self.$modal.find('#cancel').off('click.close');
            self.$modal.find('#cancel').on('click.close', function (event) {
                self.caller.set_box_free(self.move_line);
                self.caller.destroy();
                self.caller.start();
                self.$modal.modal('hide');

            });
        },
    });

    instance.stock_irm.modal.box_barcode_modal = box_barcode_modal;


    var validate_claim_line_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Validate Move';
            self.block_modal = true;
            self.template = 'validate_claim_line';
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
            console.log(self.caller);
            self.move_line = move_line;
            self.product = product;
            self._super();
            self.add_listener_on_validate();
        },
        add_listener_on_validate: function(){
            var self = this;
            self.$modal.find('#validate').off('click.validate');
            self.$modal.find('#validate').on('click.validate', function (event) {
                self.session.rpc('/rma_screen/process_picking_line', {
                    qty: self.move_line.quantity_already_scanned,
                    picking_line_id: self.move_line.id,
                    box_name: self.move_line.box,
                    packing_order_id: self.packing_order_id,
                    cart_id: self.caller.cart.id,
                }).then(function(data){
                    if (data.status == 'ok'){
                        self.$modal.modal('hide');
                        self.$modal.on('hidden.bs.modal', function () {
                            self.$modal.off();
                            var modal = new instance.stock_irm.modal.select_next_destination_modal();
                            modal.start(self.caller, data.destination, self.move_line, self.product);
                        })
                    } else {
                        self.display_error('Error', 'Could not process this picking line');
                    }
                }, function(data){
                    self.request_error(data);
                });
            })
        },
    });

    instance.stock_irm.modal.validate_claim_line_modal = validate_claim_line_modal;

    var select_next_destination_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Destination of this package';
            self.template = 'select_next_destination';
            self.block_modal = true;
        },
        start: function (caller, destination, move_line, product) {
            var self = this;
            self.$body = $(QWeb.render(self.template, {
                destination: destination
            }));
            self.$footer = $(QWeb.render('select_next_destination_footer'));
            self.caller = caller;
            self.move_line = move_line;
            self.product = product;

            self._super();
            self.add_listener_on_confirm(move_line);
        },
        add_listener_on_confirm: function(move){
            var self = this;

            self.$modal.find('#confirm_next_destination').off('click.destination');
            self.$modal.find('#confirm_next_destination').on('click.destination', function (event) {
                console.log(self.caller);
                self.$modal.modal('hide');
                self.caller.destroy();
                self.caller.start();
            })
        },
        do_after_set_box: function(box, move_line){
            var self = this;
            self.caller.add_product(self.product, self.leftover, move_line);
        },
    });

    instance.stock_irm.modal.select_next_destination_modal = select_next_destination_modal;

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
        start: function (show_cancel) {
            var self = this;
            self.$footer = $(QWeb.render(self.footer_template));
            self.$body = "<i class='fa fa-times fa-10x' style='color:red'></i><b style='font-size: 2em'>"+self.message+"</b>";
            this._super();
            self.add_listener_on_select_another(show_cancel);
        },
        add_listener_on_select_another: function(show_cancel){
            var self = this;
            self.$modal.find('#select_another').off('click.another');
            self.$modal.find('#select_another').on('click.another', function(event){
                var modal = new instance.stock_irm.modal.box_barcode_modal(self.caller, self.move_line, self.callback);
                modal.start(show_cancel);
            });
        },
    });

    instance.stock_irm.modal.box_already_used = box_already_used;

})();
