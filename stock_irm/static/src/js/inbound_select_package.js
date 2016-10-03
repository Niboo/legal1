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

    var package_selector = instance.stock_irm.widget.extend({
        init: function () {
            this._super();
            var self = this;

            QWeb.add_template('/stock_irm/static/src/xml/inbound_select_package.xml', function(){
                self.start();
            });
            self.template = 'select_package_screen_layout';
            self.scanned_package_barcodes = [];
            self.scanned_package_ids = [];
        },
        start: function() {
            var self = this;
            self._super();

            self.$change_cart = self.$nav.find('#change-cart');
            self.$change_cart.show();

            if(self.cart === undefined){
                self.get_carts(true);
            }
        },
        get_carts: function (block_modal) {
            var self = this;
            self.session.rpc('/select_package/get_carts').then(function (data) {
                if(data.status == 'ok'){
                    var modal = new instance.stock_irm.modal.select_cart_modal(block_modal);
                    modal.start(self, data.carts);
                } else {
                    self.display_error('Error', 'Could not retrieve carts');
                }
            }, function(data){
                self.request_error(data);
            });
        },
        set_cart: function (cart) {
            var self = this;
            self.cart = cart;
            self.$change_cart.html(QWeb.render('cart_navbar_item', {'cart': self.cart}));

            self.$elem = $(QWeb.render(self.template));
            $('#content').html(self.$elem);
            self.add_listener_on_numpad();
        },
        move_to_cart: function(package){
            var self = this;
            self.session.rpc('/select_package/move_to_cart', {
                cart_id: self.cart.id,
                package_id: package.id,
            }).then(function (data) {
                if (data.status == "ok") {
                    var $package_ribbon = self.$elem.find('.ok_ribbon[data-package-id="' + package.id + '"]');
                    $package_ribbon.append(self.cart.name);
                    $package_ribbon.removeClass('hidden');
                } else {
                    self.display_error('Error', 'Could not move packages to cart');
                }
            }, function(data){
                self.request_error(data);
            });
        },
        process_barcode: function(barcode){
            var self = this;
            var true_barcode = barcode.replace(/[\s]*/g, '');

            // check if we didnt already scanned the package to avoid adding the same package twice
            if($.inArray(true_barcode, self.scanned_package_barcodes) == -1){
                self.session.rpc('/select_package/get_package', {
                    barcode: true_barcode,
                }).then(function(data){
                    if(data.status == "ok"){
                        self.scanned_package_barcodes.push(true_barcode);
                        self.$elem.find('.btn-to-wave').show();
                        self.$elem.find('#message_box').hide();
                        self.scanned_package_ids.push(data.scanned_package.id);
                        var $new_box = $(QWeb.render("package_result", {
                            product_name: data.product.name,
                            quantity: data.product.quantity,
                            package_id: data.scanned_package.id,
                            package_barcode: data.scanned_package.barcode,
                            product_image: data.product.image,
                            product_quantity: data.product.quantity,
                        }));
                        self.$elem.find('.btn-to-wave').show();
                        self.$elem.find('#package_list').append($new_box);
                        self.move_to_cart(data.scanned_package);
                    } else {
                        self.display_error(data.error, data.message);
                    }
                }, function(data){
                    self.request_error(data);
                });
            }
        },
        add_listener_on_numpad: function(){
            var self = this;
            self.$elem.find('.num-pad .circle').off('click.numpad');
            self.$elem.find('.num-pad .circle').on('click.numpad', function (event) {
                var $target = $(event.currentTarget);
                value = $target.find("span").text();
                if(value=="C"){
                   self.$elem.find('#manual-barcode').val("");
                }else if(value=="Enter"){
                    self.process_barcode(self.$elem.find('#manual-barcode').val());
                    self.$elem.find('#manual-barcode').val("");
                }else{
                    self.$elem.find('#manual-barcode').val(self.$elem.find('#manual-barcode').val()+value);
                }
                $(':focus').blur()

            });
        },
    });

    instance.stock_irm.package_selector = new package_selector();
})();
