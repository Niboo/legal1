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
        init: function () {
            var self = this;
            this._super();
            self.title = 'Box is complete';
            self.block_modal = true;
        },
        start: function (barcode_type, barcode) {
            var self = this;
            self.$body = "<i class='fa fa-check fa-10x' style='color:red'></i><b style='font-size: 2em'>Put the box in the output zone.</b>";
            self.$footer = "<a href='#' class='btn btn-lg btn-success'>Continue</a>";
            this._super();
        },
    });

    instance.stock_irm.modal.complete_modal = complete_modal;

    var incomplete_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            this._super();
            self.title = 'Box is incomplete';
            self.block_modal = true;
        },
        start: function (barcode_type, barcode) {
            var self = this;
            self.$body = "<i class='fa fa-times fa-10x' style='color:red'></i><b style='font-size: 2em'>Let the box be handled by the picker.</b>";
            self.$footer = "<a href='#' class='btn btn-lg btn-success'>Continue</a>";
            this._super();
        },
    });

    instance.stock_irm.modal.incomplete_modal = incomplete_modal;

})();
