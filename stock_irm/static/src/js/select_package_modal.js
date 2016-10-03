///////////////////////////////////////////////////////////////////////////////
//
//    Author: Jérôme Guerriat
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
            self.$body.find('.cart a').off('click');
            self.$body.find('.cart a').on('click', function (e) {
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

    var confirm_bandup_wave_modal = instance.stock_irm.modal.widget.extend({
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

    instance.stock_irm.modal.confirm_bandup_wave_modal = confirm_bandup_wave_modal;

    var barcode_error_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Barcode Error';
            self.block_modal = false;
        },
        start: function (barcode_type, barcode) {
            var self = this;
            self.$body = "<i class='fa fa-times fa-10x' style='color:red'></i><b style='font-size: 2em'>Please scan the "+barcode_type+" with barcode "+barcode+".</b>";
            this._super();
        },
    });

    instance.stock_irm.modal.barcode_error_modal = barcode_error_modal;

    var complete_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            this._super();
            self.title = 'Box is complete';
            self.block_modal = false;
            self.caller = caller;
        },
        start: function () {
            var self = this;
            self.$body = "<i class='fa fa-check fa-10x' style='color:green'></i><b style='font-size: 2em'>Put the box in the output zone.</b>";
            // self.$footer = "<a href='#' class='btn btn-lg btn-success'>Continue</a>";
            this._super();
            self.add_listener_on_close_modal();
        },
        add_listener_on_close_modal: function(){
            var self = this;
            self.$modal.off('hidden.bs.modal');
            self.$modal.on('hidden.bs.modal', function () {
                self.caller.add_listener_for_barcode();
            })
        }
    });

    instance.stock_irm.modal.complete_modal = complete_modal;

    var incomplete_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            this._super();
            self.title = 'Box is incomplete';
            self.block_modal = false;
            self.caller = caller;
        },
        start: function (barcode_type, barcode) {
            var self = this;
            self.$body = "<i class='fa fa-times fa-10x' style='color:red'></i><b style='font-size: 2em'>Let the box be handled by the picker.</b>";
            // self.$footer = "<a href='#' class='btn btn-lg btn-success'>Continue</a>";
            this._super();
            self.add_listener_on_close_modal();
        },
        add_listener_on_close_modal: function(){
            var self = this;
            self.$modal.off('hidden.bs.modal');
            self.$modal.on('hidden.bs.modal', function () {
                self.caller.add_listener_for_barcode();
            })

        }
    });

    instance.stock_irm.modal.incomplete_modal = incomplete_modal;

    var in_progress_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'In progress';
            self.block_modal = true;
        },
        start: function (barcode_type, barcode) {
            var self = this;
            self.$body = "<i class='fa fa-spinner fa-pulse fa-3x fa-fw' style='color:grey;text-align:middle;font-size:2em;'></i><b style='font-size: 2em;margin-left:1em;'>Getting packages...</b>";
            this._super();
        },
    });

    instance.stock_irm.modal.in_progress_modal = in_progress_modal;

})();
