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

})();
