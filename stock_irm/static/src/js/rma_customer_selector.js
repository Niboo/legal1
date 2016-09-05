///////////////////////////////////////////////////////////////////////////////
//
//    Author: Pierre Faniel
//    Copyright 2016 Niboo SPRL
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

    var rma_customer_selector = instance.stock_irm.widget.extend({
    	init: function () {
            this._super();
            var self = this;

            QWeb.add_template('/stock_irm/static/src/xml/inbound.xml', function(){
                self.start();
            });
            self.template = 'customer_selector';
        },
        start: function(){
            var self = this;
            self._super();
            self.$elem = $(QWeb.render(this.template));
            $('#content').html(self.$elem);

            self.$elem.find('#search_bar').keyup(function(event){
                self.get_customers(event.currentTarget.value)
            });
            self.get_customers();
        },
        add_listener_on_customer: function(){
            var self = this;
            self.$elem.find('#results a').click(function(e){
                if($('#change-worklocation').attr('data-id')){
                    var customer_id = $(this).attr('data-id');
                    self.customer_id = customer_id;

                    self.session.rpc('/rma_screen/search_customer_claims', {
                        customer_id: customer_id
                    }).then(function (data) {
                        if (data.status == 'ok') {
                            var modal = new instance.stock_irm.modal.crm_claim_modal(self);
                            modal.start(data.claims);
                        } else {
                            var modal = new instance.stock_irm.modal.exception_modal();
                            modal.start(data.error, data.message);
                        }
                    });

                }else{
                    self.get_worklocations("You must select a worklocation first!", true);
                }

            })
        },
        get_claim_move_lines: function(claim_ids){
            var self = this;
            self.claim_ids = claim_ids;

            self.session.rpc('/rma_screen/get_claim_move_lines', {
                claim_ids: self.claim_ids
            }).then(function (data) {
                if(data.status == 'ok'){
                    self.claim_move_lines = data.claim_move_lines;
                    var ProductPicking = instance.stock_irm.rma_product_picking;
                    self.product_picking = new ProductPicking(self.customer_id, self.claim_ids, self.claim_move_lines);
                    self.product_picking.start();
                    self.$nav.find('#back').show();
                    self.$nav.find('#search').show();
                    self.$nav.find('#confirm').show();
                }
            });
        },
        get_customers: function(search){
            var self = this;
            self.session.rpc('/rma_screen/get_customers', {
                search: search
            }).then(function(data){
                if(data.status == 'ok'){
                    self.customers = data.customers;
                    var $result = $(QWeb.render('supplier_result', {
                        suppliers: self.customers
                    }));
                    self.$elem.find('#results').html($result);
                    self.add_listener_on_customer();
                }
            });
        },

    });
    instance.stock_irm.rma_customer_selector = new rma_customer_selector();

})();
