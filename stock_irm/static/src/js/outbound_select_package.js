///////////////////////////////////////////////////////////////////////////////
//
//    Author: Tobias Zehntner
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
    var QWeb = instance.qweb;
    instance.index = {}

    var package_selector = instance.stock_irm.widget.extend({
        init: function () {
            this._super();
            var self = this;

            QWeb.add_template('/stock_irm/static/src/xml/outbound_select_package.xml', function(){
                self.start();
            });
            self.template = 'outbound_select_package_layout';
            self.scanned_package_barcodes = [];
            self.package_ids_to_scan = [];
        },
        start: function() {
            var self = this;
            self._super();
            self.$elem = $(QWeb.render(self.template));
            $('#content').html(self.$elem);
            self.add_listener_on_numpad();
        },
        process_barcode: function(barcode){
            var self = this;
            var true_barcode = barcode.replace(/[\s]*/g, '');
            // check if we didnt already scanned the package to avoid adding the same package twice
            if($.inArray(true_barcode, self.scanned_package_barcodes) == -1){
                self.session.rpc('/outbound_select_package/process_package', {
                    barcode: true_barcode,
                }).then(function(data){
                    if(data.status == "ok"){
                        self.scanned_package_barcodes.push(data.barcode);
                        self.package_ids_to_scan.splice(
                            self.package_ids_to_scan.map(function(object) {
                                return object.package.barcode; })
                            .indexOf(data.barcode),1);

                        // Grey out scanned package on the screen
                        var box_div = 'div[data-package-id="' + data.id + '"]';
                        self.$elem.find(box_div).animate({opacity: '0.4'});

                        // If there are no more packages in this cart
                        if (self.package_ids_to_scan.length == 0) {
                            var modal = new instance.stock_irm.modal.confirm_bandup_wave_modal();
                            modal.start();
                            window.setTimeout(function () {
                                window.location.href = "/outbound_select_package";
                            }, 3000);
                        }

                    } else {
                        var modal = new instance.stock_irm.modal.exception_modal();
                        modal.start(data.error, data.message);
                    }
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
                $(':focus').blur();
            });
        },
    });

    instance.stock_irm.package_selector = new package_selector();
})();
