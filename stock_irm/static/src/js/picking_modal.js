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

    var picking_modal = instance.stock_irm.modal.widget.extend({
        init: function (title) {
            var self = this;
            this._super();
            self.body_template = 'picking_info';
            self.title = title;
        },
        start: function (products) {
            var self = this;
            self.$body = $(QWeb.render(self.body_template, {
                'products': products,
            }));
            this._super();
        }
    });

    instance.stock_irm.modal.picking_modal = picking_modal;

    var select_wave_template = instance.stock_irm.modal.widget.extend({
        init: function(caller, wave_templates){
            var self = this;
            this._super();
            self.title = 'Select Wave Template';
            self.block_modal = true;
            self.template = 'select_wave_template';
            self.template_footer = 'select_wave_template_footer';
            self.wave_templates = wave_templates;
            self.caller = caller
        },
        start: function(){
            var self = this;
            self.$body = $(QWeb.render(self.template, {
                wave_templates: self.wave_templates
            }));
            self.$footer = $(QWeb.render(self.template_footer))
            this._super();
            self.add_listener_on_wave_template();
        },
        add_listener_on_wave_template: function(){
            var self = this;
            self.$modal.find('.template').click(function(event){
                var $button = $(event.currentTarget);
                var id = $button.attr('id');
                var wave_template = self.wave_templates[id];

                self.$modal.modal('hide');
                self.caller.get_waves(wave_template);
            });
        }
    });

    instance.stock_irm.modal.select_wave_template = select_wave_template;

    var end_wave_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            this._super();
            self.caller = caller;
            self.title = 'Wave Finished!';
        },
        start: function (time, pickings) {
            var self = this;
            self.pickings = pickings;
            self.$body = "<i class='fa fa-check fa-5x' style='color:green'></i>" +"<b style='font-size: 2em'>Wait for redirection...</b>";
            self.$footer = "<b style='font-size: 3em;'>Time to complete: </b><b class='time-complete'>"+time+" minutes</b>";
            this._super();

            window.setTimeout(function(){
                window.location.href = "/picking_waves";
            }, 3000);

            //window.setTimeout(function(){
            //    var to_outputs = [];
            //    var to_temps = [];
            //
            //    $.each(self.pickings, function(key, value){
            //        if(value['progress_done']<100){
            //            to_temps.push(value);
            //        } else {
            //            to_outputs.push(value);
            //        }
            //    });
            //
            //    self.$modal.modal('hide');
            //    self.$elem = $(QWeb.render("wave_done", {
            //        to_outputs: to_outputs,
            //        to_temps: to_temps,
            //    }));
            //    $('#content').html(self.$elem);
            //    self.caller.add_listener_on_endbox();
            //}, 3000);

        },
    });

    instance.stock_irm.modal.end_wave_modal = end_wave_modal;

    var wrong_quantity_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.body_template = 'counter_error';
            self.title = 'Item Count Error';
        },
        start: function (real, expected) {
            var self = this;
            self.$body = $(QWeb.render(self.body_template, {
                'real': real,
                'expected': expected
            }));
            this._super();
        },
    });

    instance.stock_irm.modal.wrong_quantity_modal = wrong_quantity_modal;

    var error_modal = instance.stock_irm.modal.widget.extend({
        init: function (title) {
            var self = this;
            this._super();
            self.body_template = 'print_error_message';
            self.title = title;
        },
        start: function (type, location, image) {
            var self = this;
            if(type == 'product'){
                self.$body = $(QWeb.render(self.body_template, {
                    'type': type,
                    'image': image,
                    'location': location,
                }));
            } else {
                self.$body = $(QWeb.render(self.body_template, {
                    'type': type,
                    'dest_location': location,
                }));
            }

            this._super();
        },
    });

    instance.stock_irm.modal.error_modal = error_modal;

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
                window.location.href = "/picking_waves";
            })
        },
        add_listener_on_continue_button: function(){
            var self = this;
            self.$modal.find('#continue_wave').click(function(event){
                self.$modal.modal('hide');
            })
        },
    });

    instance.stock_irm.modal.back_modal = back_modal;

    var select_cart_modal = instance.stock_irm.modal.widget.extend({
        template: 'cart_result_body',
        init: function () {
            var self = this;
            this._super();
            self.title = 'Select a cart';
            self.block_modal = true;
        },
        start: function (caller, carts) {
            var self = this;
            self.caller = caller;
            self.carts = carts;
            self.$body = $(QWeb.render(self.template, {
                carts: carts,
            }));
            self.footer_template = 'generic_confirm_button';
            self._super();
            self.add_listener_on_cart_button();
        },
        add_listener_on_cart_button: function () {
            var self = this;
            self.$body.find('.cart a').off('click');
            self.$body.find('.cart a').on('click', function (e) {
                self.caller.cart_id = parseInt($(this).attr('cart-id'));
                self.$modal.modal('hide');
                self.$modal.on('hidden.bs.modal', function () {
                    self.caller.display_page();
                    self.$modal.off();
                    self.caller.add_listener_for_barcode();
                });
            })
        }
    });

    instance.stock_irm.modal.select_cart_modal = select_cart_modal;

    var package_not_found = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.body_template = 'package_not_found_modal';
            self.title = "Package Not Found";
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.body_template));
            this._super();
        },
    });

    instance.stock_irm.modal.package_not_found = package_not_found;

    var scan_product_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.body_template = 'scan_product_modal';
            self.title = "Scan product first!";
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.body_template));
            this._super();
        },
    });

    instance.stock_irm.modal.scan_product_modal = scan_product_modal;

    var already_scanned_box = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.body_template = 'already_scanned_box';
            self.title = "Box already scanned";
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.body_template));
            this._super();
        },
    });

    instance.stock_irm.modal.already_scanned_box = already_scanned_box;

})();
