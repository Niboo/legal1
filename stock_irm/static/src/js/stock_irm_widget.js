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
    var last_key_time = 0;
    var barcode_string = "";
    instance.stock_irm = {};

    var stock_irm_widget= instance.Class.extend({
        init: function () {
            var self = this;

            self.session = new instance.Session();
            self.$nav = $('nav');
            self.$modal = $('#modalWindow');

            self.add_listeners();
        },
        add_listener_on_search_button: function(){
            var self = this;
            self.$nav.off('click.search');
            self.$nav.find('#search a').hide();
        },
        add_listener_on_back_button: function(){
            var self = this;
            self.$nav.off('click.back');
            self.$nav.find('#back a').hide();
        },
        add_listener_on_confirm_button: function(){
            var self = this;
            self.$nav.off('click.confirm');
            self.$nav.find('#confirm a').hide();
        },
        add_barcode_listener: function(){
            var self = this;
            var pressed = false;
            var chars = [];
            $(document).off('keypress.barcode');
            $(document).on('keypress.barcode', function(e) {
                chars.push(String.fromCharCode(e.which));
                if (pressed == false) {
                    setTimeout(function(){
                        if (chars.length >= 6) {
                            var barcode = chars.join("");
                            self.process_barcode(barcode)
                        }
                        chars = [];
                        pressed = false;
                    },500);
                }
                pressed = true;
            });
        },
        process_barcode: function(barcode){
            // dummy method to process barcode
            console.log("Barcode Scanned: " + barcode);
        },
        add_listeners: function(){
            var self = this;
            self.add_listener_on_back_button();
            self.add_listener_on_search_button();
            self.add_listener_on_confirm_button();
            self.add_barcode_listener();
        },
        show_modal: function(title, content){
            var self = this;
            self.$modal.find('.modal-title').html(title);
            self.$modal.find('.modal-body').html(content);
            self.$modal.modal("show");
        },
        destroy: function(){
        },
    });

    instance.stock_irm.widget = stock_irm_widget
})();
