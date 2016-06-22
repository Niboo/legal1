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
    instance.index = {}

    var index_selector = instance.stock_irm.widget.extend({
        init: function () {
            this._super();
            var self = this;

            QWeb.add_template('/stock_irm/static/src/xml/bandup.xml', function(){
                self.start();
            });
            self.template = 'bandup_screen_layout';
            self.scanned_package_barcodes = [];
            self.scanned_package_ids = [];
        },
        start: function(){
            var self = this;
            var $result = $(QWeb.render(self.template));

            $('#content').html($result);
            this._super();
            self.add_listener_on_goto_wave();
        },
        process_barcode: function(barcode){
            var self = this;
            var true_barcode = barcode.replace(/[\n\r]+/g, '');

            // check if we didnt already scanned the package to avoid adding the same package twice
            if($.inArray(true_barcode, self.scanned_package_barcodes) == -1){
                self.session.rpc('/bandup/get_package', {
                    barcode: true_barcode,
                }).then(function(data){
                    console.log(data);
                    if(data.status == "ok"){
                        self.scanned_package_barcodes.push(true_barcode);
                        self.scanned_package_ids.push(data.scanned_package.id);
                        var $new_box = $(QWeb.render("package_result", {
                            product_name: data.product.name,
                            quantity: data.product.quantity,
                            package_id: data.scanned_package.id,
                            package_barcode: data.scanned_package.barcode,
                            product_image: data.product.image,
                            product_quantity: data.product.quantity,
                        }));
                        $('#package_list').append($new_box);
                    }
                });
            }
        },
        add_listener_on_goto_wave: function(){
            var self = this;
            $('#content').off('click.gotowave');
            $('#content').on('click.gotowave', '#goto_wave', function (event) {
                self.session.rpc('/bandup/transfert_package_batch', {
                    package_ids: self.scanned_package_ids,
                })
            })
        },
    });
    instance.index.picking_selector = new index_selector();
})();
