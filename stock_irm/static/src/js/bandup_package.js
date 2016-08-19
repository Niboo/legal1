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

    var bandup_selector = instance.stock_irm.widget.extend({
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
        start: function() {
            var self = this;
            self._super();

            self.session.rpc('/inbound_wave/get_wave_template', {}).then(function (data) {
                if (data.status == "ok") {
                    var modal = new instance.stock_irm.modal.select_wave_template(self, data.wave_templates);
                    modal.start();
                }
            });
        },
        get_waves: function(wave_template){
            var self = this;

            self.wave_template = wave_template;

            self.session.rpc('/inbound_wave/get_inbound_wave', {
                wave_template_id: self.wave_template.id
            }).then(function(data){
                if(data.status=="ok"){
                    var $result = $(QWeb.render(self.template, {
                        'waves': data.waves,
                    }));
                    self.step = "bandup";

                    $('#content').html($result);
                    self.add_listener_on_existing_waves();
                    self.add_listener_on_goto_wave();
                    self.add_listener_on_numpad();
                }
            });
        },
        process_barcode: function(barcode){
            var self = this;
            var true_barcode = barcode.replace(/[\s]*/g, '');

            // check if we didnt already scanned the package to avoid adding the same package twice
            if($.inArray(true_barcode, self.scanned_package_barcodes) == -1){
                self.session.rpc('/bandup/get_package', {
                    barcode: true_barcode,
                    wave_template_id: self.wave_template.id
                }).then(function(data){
                    if(data.status == "ok"){
                        self.scanned_package_barcodes.push(true_barcode);
                        $("#existing_waves_div").hide();
                        $("#goto_wave").show();
                        $('#message_box').hide();
                        self.scanned_package_ids.push(data.scanned_package.id);
                        var $new_box = $(QWeb.render("package_result", {
                            product_name: data.product.name,
                            quantity: data.product.quantity,
                            package_id: data.scanned_package.id,
                            package_barcode: data.scanned_package.barcode,
                            product_image: data.product.image,
                            product_quantity: data.product.quantity,
                        }));
                        $('#goto_wave').show();
                        $('#package_list').append($new_box);
                    } else {
                        var modal = new instance.stock_irm.modal.exception_modal();
                        modal.start(data.error, data.message);
                    }
                });
            }
        },
        add_listener_on_goto_wave: function(){
            var self = this;
            $('#content').off('click.gotowave');
            $('#content').on('click.gotowave', '#goto_wave', function (event) {
                self.session.rpc('/bandup/transfer_package_batch', {
                    package_ids: self.scanned_package_ids,
                    wave_template_id: self.wave_template.id,
                }).then(function(data){
                    if(data.status == 'ok'){
                        var bandup_wave_widget = new instance.stock_irm.bandup_waves(data.package_list)
                        bandup_wave_widget.start();
                    } else {
                        var modal = new instance.stock_irm.modal.exception_modal();
                        modal.start(data.error, data.message);
                    }
                });
            })
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
        add_listener_on_existing_waves: function(){
            var self = this;

            $('.wave-div a').off('click.existing_wave');
            $('.wave-div a').on('click.existing_wave', function (event) {
                var wave_id = $(event.currentTarget).attr('wave-id');
                self.session.rpc('/bandup/get_wave', {
                    'wave_id': wave_id,
                }).then(function(data){
                    if(data.status=="ok"){
                        var bandup_wave_widget = new instance.stock_irm.bandup_waves(data.package_list)
                        bandup_wave_widget.start();
                    }
                })
        })},
    });

    instance.stock_irm.bandup_selector = new bandup_selector();
})();
