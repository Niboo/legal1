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

    instance.stock_irm = {};

    var stock_irm_widget= instance.Class.extend({
        init: function () {
            var self = this;

            self.session = new instance.Session();
            self.$nav = $('nav');

            self.add_listener_on_back_button();
            self.add_listener_on_search_button();
        },
        add_listener_on_back_button: function(){
            var self = this;
            self.$nav.off('click.back');
            self.$nav.on('click.back', '#back a', function(event){
                console.log('back');
            })
        },
        add_listener_on_search_button: function(){
            var self = this;
            self.$nav.off('click.search');
            self.$nav.on('click.search', '#search a', function(event){
                console.log('search');
            })
        },
        add_listeners: function(){
            var self = this;
            self.add_listener_on_back_button();
            self.add_listener_on_search_button();
        },
        destroy: function(){
        },
    });

    instance.stock_irm.widget = stock_irm_widget
})();
