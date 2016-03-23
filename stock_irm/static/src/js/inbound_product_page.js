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

    var inbound_product_page = instance.stock_irm.widget.extend({
    	init: function (parent, id) {
            this._super();
            var self = this;
            self.id = id;
            self.template = 'product_page';
            self.parent = parent;
        },
        start: function(){
            var self = this;
            self.get_product();
        },
        add_listener_on_quantity: function(){
            var self = this;
            self.$elem.find('#quantity button').click(function(event){
                qty = $('#quantity input').val();
                if($(event.currentTarget).attr('data-dir') == 'up'){
                    $('#quantity input').val(parseInt(qty) + 1);
                } else {
                    if(qty > 1){
                        $('#quantity input').val(parseInt(qty) - 1);
                    }
                }
            });
        },
        get_product: function(){
            var self = this;

            self.session.rpc('/inbound_screen/get_product', {
                id: self.id,
                supplier_id: self.parent.supplier_id
            }).then(function(data){
                self.$elem = $(QWeb.render(self.template, {
                    product: '/stock_irm/static/img/product1.jpg',
                    product: data.product
                }));
                $('body').html(self.$elem);
                self.add_listener_on_quantity();
            })
        }
    });

    instance.stock_irm.inbound_product_page = inbound_product_page;

})();
