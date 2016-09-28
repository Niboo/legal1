///////////////////////////////////////////////////////////////////////////////
//
//    Author: Jérôme Guerriat
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

    var inventory_page = instance.stock_irm.widget.extend({
        init: function () {
            this._super();
            var self = this;
            self.location_id = false;
            self.product_id = false;
            self.template = 'inventory_layout';
            QWeb.add_template('/stock_irm/static/src/xml/inventory.xml', function(){
                self.start();
            });


        },
        start: function() {
            var self = this;
            console.log("start")
            self._super();
            self.$elem = $(QWeb.render(self.template));
            $('#content').html(self.$elem);

            self.add_listener_for_barcode();
            self.add_listener_on_numpad();
        },
        add_listener_on_numpad: function(){
            var self = this;
            $('.num-pad .circle').off('click.numpad');
            $('.num-pad .circle').on('click.numpad', function (event) {
                var $target = $(event.currentTarget);
                value = $target.find("span").text();
                if(value=="C"){
                   $('#manual-barcode').val("");
                }else if(value=="Enter"){
                    self.process_barcode($('#manual-barcode').val());
                    $('#manual-barcode').val("");
                }else{
                    $('#manual-barcode').val($('#manual-barcode').val()+value);
                }
                $(':focus').blur()
            });
        },
        process_barcode: function(barcode) {
            var self = this;

            barcode = barcode.replace(/[\s]*/g, '');

            if(!self.location_id){
                console.log("apres")

                self.session.rpc('/inventory_update/get_location', {
                    'barcode': barcode
                }).then(function(data){
                    if(data.status == "ok"){
                        self.location_id = data.location_id;
                        self.$elem.find('#message_box').switchClass("alert-warning", "alert-info", 100)
                    }else{
                        var modal = new instance.stock_irm.modal.not_found_modal();
                        modal.start(data.message);
                    }
                });
            }else if(!self.product_id){
                self.session.rpc('/inventory_update/get_product', {
                    'barcode': barcode
                }).then(function(data){
                    if(data.status == "ok"){
                        self.product_id = data.product_id;
                    }else{
                        var modal = new instance.stock_irm.modal.not_found_modal();
                        modal.start(data.message);
                    }
                });
            }
        },
    });

    instance.stock_irm.inventory_page = new inventory_page();
})();
