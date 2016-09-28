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

    var not_found_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Barcode not found';
            self.block_modal = false;
        },
        start: function (message) {
            var self = this;
            self.$body = "<i class='fa fa-times fa-10x' style='color:red'></i><b style='font-size: 2em'>"+message+"</b>";
            this._super();
            self.add_listener_on_close();
        },
        add_listener_on_close: function(){
            var self = this;
            self.$modal.find('#close').click(function(event){
                self.$modal.modal('hide');
            })
        },
    });

    instance.stock_irm.modal.not_found_modal = not_found_modal;

    var confirm_update_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Inventory Update Confirmed!';
            self.block_modal = true;
        },
        start: function () {
            var self = this;
            self.$body = "<i class='fa fa-check fa-10x' style='color:green'></i><b style='font-size: 2em'>Wait for redirection...</b>";
            this._super();
        },
    });

    instance.stock_irm.modal.confirm_update_modal = confirm_update_modal;

    var error_modal_inventory = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'An error occured';
            self.block_modal = false;
        },
        start: function (message) {
            var self = this;
            self.$body = "<i class='fa fa-times fa-10x' style='color:red'></i><b style='font-size: 2em'>"+message+"</b>";
            this._super();
            self.add_listener_on_close();
        },
        add_listener_on_close: function(){
            var self = this;
            self.$modal.find('#close').click(function(event){
                self.$modal.modal('hide');
            })
        },
    });

    instance.stock_irm.modal.error_modal_inventory = error_modal_inventory;

})();
