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

    var picking_selector = instance.picking_waves.widget.extend({
    	init: function () {
            this._super();
            var self = this;

            QWeb.add_template('/stock_irm/static/src/xml/picking.xml', function(){
                self.start();
            });
            self.template = 'go_picking';
        },
        start: function(){
            var self = this;
            self.$elem = $(QWeb.render(this.template));
            $('#content').html(self.$elem);
            self.add_listener_on_supplier();
        },
        add_listener_on_supplier: function(){
            var self = this;
            self.$elem.find('#create-wave').click(function(event){
                self.session.rpc('/picking_waves/create_picking', {
                }).then(function(data){
                    console.log("then");
                });
            })
        },
    });
    instance.picking_waves.picking_selector = new picking_selector();
})();
