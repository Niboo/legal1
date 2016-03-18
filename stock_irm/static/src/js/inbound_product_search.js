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

    var inbound_product_search = instance.stock_irm.widget.extend({
    	init: function () {
            this._super();
            var self = this;
            this.template = 'product_selector';
        },
        start: function(){
            var self = this;
            self.$elem = $(QWeb.render(this.template));
            $('body').html(self.$elem);

            self.$elem.find('#search').keyup(function(event){
                if(event.currentTarget.value.length > 5 | event.which == 13 ){
                    self.get_products(event.currentTarget.value)
                }
            })
        },
        get_products: function(search){
            var self = this;
            self.session.rpc('/inbound_screen/get_products_data', {
                search: search
            }).then(function(data){
                    self.products = data.products;
                    var $result = $(QWeb.render('product_result', {
                            products: self.products
                    }));
                    self.$elem.find('#results').html($result);
                });
        },
    });

    instance.stock_irm.inbound_product_search = new inbound_product_search();

})();
