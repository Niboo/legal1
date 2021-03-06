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

    var inbound_supplier_selector = instance.stock_irm.widget.extend({
    	init: function () {
            this._super();
            var self = this;

            QWeb.add_template('/stock_irm/static/src/xml/inbound.xml', function(){
                self.start();
            });
            self.template = 'supplier_selector';
        },
        start: function(){
            var self = this;
            self._super();
            self.$elem = $(QWeb.render(this.template));
            $('#content').html(self.$elem);

            self.$elem.find('#search_bar').keyup(function(event){
                self.get_suppliers(event.currentTarget.value)
            });
            self.get_suppliers();
        },
        add_listener_on_supplier: function(){
            var self = this;
            self.$elem.find('#results a').click(function(event){
                if($('#change-worklocation').attr('data-id')){
                    var supplier_id = $(event.currentTarget).attr('data-id');
                    self.supplier_id = supplier_id

                    self.session.rpc('/inbound_screen/search_supplier_purchase', {
                        supplier: supplier_id
                    }).then(function (data) {
                        if (data.status == 'ok') {
                            var modal = new instance.stock_irm.modal.purchase_order_modal(self);
                            modal.start(data.orders);
                        } else {
                            self.display_error(data.error, data.message);
                        }
                    }, function(data){
                        self.request_error(data);
                    });

                }else{
                    self.get_worklocations("You must select a worklocation first!", true);
                }

            })
        },
        get_purchase_order_move_lines: function(purchase_order_ids){
            var self = this;
            self.purchase_order_ids = purchase_order_ids;

            self.session.rpc('/inbound_screen/get_purchase_order_move_lines', {
                purchase_order_ids: self.purchase_order_ids
            }).then(function (data) {
                self.po_move_lines = data.po_move_lines;
                var ProductPicking = instance.stock_irm.inbound_product_picking;
                self.product_picking = new ProductPicking(self.supplier_id, self.purchase_order_ids, self.po_move_lines);
                self.product_picking.start();
                self.$nav.find('#back').show();
                self.$nav.find('#search').show();
                self.$nav.find('#confirm').show();
            });
        },
        get_suppliers: function(search){
            var self = this;
            self.session.rpc('/inbound_screen/get_suppliers', {
                search: search
            }).then(function(data){
                self.suppliers = data.suppliers;
                var $result = $(QWeb.render('supplier_result', {
                    suppliers: self.suppliers
                }));
                self.$elem.find('#results').html($result);
                self.add_listener_on_supplier();
            });
        },

    });
    instance.stock_irm.inbound_supplier_selector = new inbound_supplier_selector();

})();
