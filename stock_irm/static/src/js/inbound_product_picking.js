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

    var inbound_product_picking = instance.stock_irm.widget.extend({
    	init: function (supplier_id) {
            this._super();
            var self = this;
            self.template = 'product_selector';
            self.supplier_id = supplier_id;
        },
        start: function(){
            var self = this;
            self.$elem = $(QWeb.render(this.template));
            $('body').html(self.$elem);
            self.add_listener_on_search();
        },
        add_listener_on_search: function(){
            var self = this;
            self.$elem.find('#search').keyup(function (event) {
                if (self.search != event.currentTarget.value
                        & event.currentTarget.value.length > 5
                        | event.which == 13) {
                    self.page = 1;
                    self.$elem.find('#results').empty();
                    self.search = event.currentTarget.value;
                    self.get_products();
                }
            });
        },
        add_listener_on_more: function(){
            var self = this;
            self.$elem.find('#more').click(function(event){
                event.preventDefault();
                self.page += 1;
                self.get_products();
            })
        },
        add_listener_on_product: function($result){
            var self = this;
            $result.find('a').click(function(event){
                var product_id = $(event.currentTarget).attr('data-id');
                var ProductPage = instance.stock_irm.inbound_product_page;
                self.product_page = new ProductPage(self, product_id);
                self.product_page.start();
            })
        },
        get_products: function(){
            var self = this;
            self.session.rpc('/inbound_screen/get_products', {
                supplier_id: self.supplier_id,
                search: self.search,
                page: self.page - 1
            }).then(function(data){
                self.products = data.products;
                var $result = $(QWeb.render('product_result', {
                    products: self.products,
                }));

                self.add_listener_on_product($result);
                self.$elem.find('#results').append($result);

                self.$elem.find('#more').remove();

                if(data.products_count > data.search_limit * self.page){
                    var $more = $(QWeb.render('result_more', {}));
                    self.$elem.find('#results').append($more);
                    self.add_listener_on_more();
                }
            });
        },
    });

    instance.stock_irm.inbound_product_picking = inbound_product_picking;

})();
