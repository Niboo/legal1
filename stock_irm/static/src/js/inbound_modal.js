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

    var no_cart_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.body_template = 'no_cart_message';
            self.title = 'Cart Error';
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.body_template));
            this._super();
        },
    });

    instance.stock_irm.modal.no_cart_modal = no_cart_modal;

    var select_cart_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller, block) {
            var self = this;
            this._super(caller);
            self.body_template = 'cart_result';
            self.title = 'Cart Selection';
            self.block_modal = block;
        },
        start: function (carts) {
            var self = this;
            self.$body = $(QWeb.render(self.body_template, {
                carts: carts,
            }));
            this._super();
            self.add_listener_on_carts();
        },
        add_listener_on_carts: function(){
            var self = this;
            self.$modal.find('.modal-body .cart').click(function(event){
                event.preventDefault();
                var cart_id = $(event.currentTarget).attr('cart-id');
                var cart_name = $(event.currentTarget).attr('cart-name');
                self.caller.parent.select_cart(cart_id, cart_name);
                self.caller.display_cart_info(true);
            });
            self.$modal.find("a[is-in-usage='true']").hide()
            self.$modal.find('input:checkbox').live('click', function () {
                if($('#display-all-cart').is(':checked')){
                    self.$modal.find("a[is-in-usage='true']").show()
                }else{
                    self.$modal.find("a[is-in-usage='true']").hide()
                }
            });
        },
    });

    instance.stock_irm.modal.select_cart_modal = select_cart_modal;

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

            self.$modal.find('#select_purchases').off('click.select_purchases');
            self.$modal.find('#select_purchases').on('click.select_purchases', function (event) {
                self.caller.set_purchase_order_lines(self.selected_purchases);
                self.$modal.modal('hide');
            });
            self.$modal.find('#no_purchases').off('click.no_purchases');
            self.$modal.find('#no_purchases').on('click.no_purchases', function (event) {
                self.caller.set_purchase_order_lines(false);
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
        init: function (caller) {
            var self = this;
            this._super(caller);
            self.body_template = 'box_barcode_modal';
            self.footer_template = 'box_barcode_footer_modal';
            self.title = 'Scan the box barcode';
            self.block_modal = true;
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.body_template));
            self.$footer = $(QWeb.render(self.footer_template));
            this._super();
            self.add_listener_on_barcode_modal_confirm();
            self.$modal.find('#box_barcode').focus();
        },
        confirm_box: function(){
            var self = this;

            var barcode = self.$modal.find('#box_barcode').val();
            if(barcode){
                self.session.rpc('/inbound_screen/check_package_empty', {
                    package_barcode: barcode
                }).then(function(data){
                    if(data.status=="ok"){
                        if (!self.caller.parent.product_in_package[barcode] || self.caller.parent.product_in_package[barcode]==self.caller.id){
                            self.caller.parent.set_box_barcode(barcode);
                            self.caller.add_listener_for_barcode();

                            // we should "predisplay" a box under the product before it is added to a box. Otherwise,
                            // worker won't be able to close the first box for a determined product.
                            self.caller.predisplay_box();
                            if(!self.caller.check_current_picking_line()){
                                self.$modal.modal('hide');
                            }
                        }else{
                            var error_modal = new instance.stock_irm.modal.box_already_used(self.caller, "This box is already filled with another product");
                            error_modal.start();
                        }
                    }else{
                        var error_modal = new instance.stock_irm.modal.box_already_used(self.caller, "This box is already used elsewhere");
                        error_modal.start();
                    }
                })
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
        init: function (caller, message) {
            var self = this;
            this._super(caller);
            self.title = 'Box already used';
            self.block_modal = true;
            self.footer_template = 'select_another_box_footer_modal';
            self.message = message;
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
                var modal = new instance.stock_irm.modal.box_barcode_modal(self.caller);
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

    var confirm_note_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Confirm Inbound Picking';
            self.block_modal = true;
            self.template = 'packing_order_note';
            self.footer_template = 'packing_order_note_footer';
        },
        start: function (caller, product_id, qty) {
            var self = this;
            self.$body = $(QWeb.render(self.template));
            self.$footer = $(QWeb.render(self.footer_template));
            self.caller = caller;
            self.product_id = product_id;
            self.qty = qty;

            self._super();
            self.add_listener_on_cancel_note();
            self.add_listener_on_confirm_note();
        },
        add_listener_on_cancel_note: function(){
            var self = this;
            self.$modal.find('#cancel_note').click(function(event){
                self.$modal.modal('hide');
            })
        },
        add_listener_on_confirm_note: function(){
            var self = this;
            self.$modal.find('#confirm_note').click(function(event){
                var note = self.$modal.find('#packing_note').val();
                self.caller.parent.add_product(self.product_id, self.qty, true, note);
                self.caller.destroy();
                self.caller.parent.refresh();
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
        },
        start: function (caller, nb_product_more, po_line, product, qty_to_add, cart_id, box_name) {
            var self = this;
            self.$body = $(QWeb.render(self.template,{
                nb_product_more: nb_product_more
            }));

            self.$footer = $(QWeb.render(self.footer_template,{
                nb_product_more: nb_product_more
            }));
            self.caller = caller;
            self.po_line = po_line;
            self.product = product;
            self.qty_to_add = qty_to_add;
            self.cart_id = cart_id;
            self.box_name = box_name;

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
                self.caller.print_missing_labels();
                self.caller.parent.add_product(self.product, self.qty_to_add);
                self.session.rpc('/inbound_screen/process_complete_picking_line', {
                    picking_line_id: self.po_line.id,
                    cart_id : self.cart_id,
                    box_name: self.box_name
                });
                self.caller.close_box_if_no_more_product(self.product);
                var modal = new instance.stock_irm.modal.select_next_destination_modal();
                modal.start(self.caller, self.po_line);
            })
        },
    });

    instance.stock_irm.modal.validate_po_line_modal = validate_po_line_modal;

    var select_next_destination_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Select Next Destination';
            self.template = 'select_next_destination';
            self.block_modal = true;

        },
        start: function (caller) {
            var self = this;

            var locations = [{'id':1,name:"test"},{'id':2,name:"testTESTtest"}];
            self.$body = $(QWeb.render(self.template, {
                locations:locations
            }));

            self.caller = caller;

            self._super();
            self.add_listener_on_locations();
        },
        add_listener_on_locations: function(){
            var self = this;

            self.$modal.find('.location_buttons').off('click.location_buttons');
            self.$modal.find('.location_buttons').on('click.location_buttons', function (event) {
                self.$modal.modal('hide');
                self.caller.destroy();
                self.caller.parent.start();
            })
        },
    });

    instance.stock_irm.modal.select_next_destination_modal = select_next_destination_modal;

    var box_barcode_modal_staging = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            this._super(caller);
            self.body_template = 'box_barcode_modal_staging';
            self.footer_template = 'box_barcode_modal_staging_footer';
            self.block_modal = true;
        },
        start: function (order_lines, title, operation, supplier_id) {
            var self = this;
            self.order_lines = order_lines;
            self.$body = $(QWeb.render(self.body_template));
            self.$footer = $(QWeb.render(self.footer_template));
            self.title = title;
            self.operation = operation;
            self.supplier_id = supplier_id

            this._super();
            self.add_listener_on_barcode_modal_confirm();
            self.$modal.find('#box_barcode').focus();
        },
        confirm_box: function(){
            var self = this;

            var barcode = self.$modal.find('#box_barcode').val();
            if(barcode){
                self.session.rpc('/inbound_screen/check_staging_package_empty', {
                    barcode: barcode
                }).then(function(data){
                    var staging_box_id = data.dest_box_id;
                    if(self.operation =="incomplete"){

                        if(data.status=="ok"){
                            self.session.rpc('/inbound_screen/move_uncomplete_line_to_staging', {
                                uncomplete_order_line: self.order_lines,
                                dest_box_id: staging_box_id,
                                supplier_id: self.supplier_id,

                            })
                        }else{
                            var error_modal = new instance.stock_irm.modal.box_already_used(self.caller, "This box is already used in staging location");
                            error_modal.start();
                        }
                    }else if(self.operation=="unordered"){
                        self.session.rpc('/inbound_screen/create_picking_for_unordered_lines', {
                            extra_lines: self.order_lines,
                            dest_box_id: staging_box_id,
                            supplier_id: self.supplier_id,
                        }).then(function(data){
                            if (data.status == 'ok'){
                                var modal = new instance.stock_irm.modal.confirmed_modal();
                                modal.start();
                                window.setTimeout(function(){
                                    window.location.href = "/inbound_screen";
                                }, 3000);
                            } else {
                                var modal = new instance.stock_irm.modal.exception_modal();
                                modal.start(data.error, data.message);
                            }
                        })
                    }
                })
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

    instance.stock_irm.modal.box_barcode_modal_staging = box_barcode_modal_staging;

})();
