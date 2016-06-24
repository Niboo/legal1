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

    var no_package_found_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Package not Found!';
            self.block_modal = false;
        },
        start: function () {
            var self = this;
            self.$body = "<i class='fa fa-times fa-10x' style='color:red'></i><b style='font-size: 2em'>Package Not Found</b>";
            this._super();
        },
    });

    instance.stock_irm.no_package_found_modal = no_package_found_modal;


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

})();
