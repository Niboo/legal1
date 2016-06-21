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
                purchase_orders: orders,
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
            self.$modal.find('#cancel').off('click.cancel');
            self.$modal.find('#cancel').on('click.cancel', function (event) {
                self.$modal.modal('hide');
            });
            self.$modal.find('#select_purchases').off('click.select_purchases');
            self.$modal.find('#select_purchases').on('click.select_purchases', function (event) {
                var note = self.$modal.find('#packing_note').val();
                self.caller.confirm(self.selected_purchases, note);
            });
            self.$modal.find('#no_purchases').off('click.no_purchases');
            self.$modal.find('#no_purchases').on('click.no_purchases', function (event) {
                var note = self.$modal.find('#packing_note').val();
                self.caller.confirm(false, note);
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
        add_listener_on_barcode_modal_confirm: function(){
            var self = this;
            self.$modal.find('#confirm_box_barcode').off('click.box.barcode');
            self.$modal.find('#confirm_box_barcode').on('click.box.barcode', function(event){
                var barcode = self.$modal.find('#box_barcode').val();
                if(barcode){
                    self.$modal.modal('hide');
                    self.caller.set_box_barcode(barcode) ;
                }
            });
        },
    });

    instance.stock_irm.modal.box_barcode_modal = box_barcode_modal;

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
            self.$body = 'All your change will be canceled';
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
})();
