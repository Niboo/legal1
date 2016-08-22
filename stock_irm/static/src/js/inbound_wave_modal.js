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

    var select_wave_template = instance.stock_irm.modal.widget.extend({
        init: function(caller, wave_templates){
            var self = this;
            this._super();
            self.title = 'Select Wave Template';
            self.block_modal = true;
            self.template = 'select_wave_template';
            self.wave_templates = wave_templates;
            self.caller = caller
        },
        start: function(){
            var self = this;
            self.$body = $(QWeb.render(self.template, {
                wave_templates: self.wave_templates
            }));
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
                self.caller.get_carts_and_waves(wave_template);
            });
        }
    });

    instance.stock_irm.modal.select_wave_template = select_wave_template;


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

})();
