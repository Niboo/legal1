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
    instance.picking_waves = {}

    var bandup_waves = instance.stock_irm.widget.extend({
        init: function (package_list) {
            this._super();
            var self = this;

            self.package_list = package_list;

            self.current_package_barcode = self.package_list[0].package_barcode;
            self.current_location_dest_barcode = self.package_list[0].location_dest_barcode;
            
            self.template = 'inbound_wave_layout';
        },
        start: function() {
            var self = this;
            self.display();
            self.step = 'package';
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
        display: function(){
            var self = this;

            var display_package_list = self.package_list.slice(1, 6);
            var $elem = $(QWeb.render(self.template, {
                'product': self.package_list[0],
                'packages': display_package_list,
            }));

            $('#content').html($elem);
            self.add_listener_on_numpad();
            var $message = $(QWeb.render('info_package_barcode'));
            $('#info_message').html($message)
        },
        process_barcode: function(barcode){
            var self = this;

            if(self.step == 'package'){
                if(barcode == self.current_package_barcode){
                    $('#pack_barcode').hide();
                    self.step = 'location';
                    var $message = $(QWeb.render('info_location_barcode'));
                    $('#info_message').html($message)
                    $("#current_product").animate({backgroundColor: "#dff0d8"}, 200);
                }else{
                    var modal = new instance.stock_irm.modal.barcode_error_modal();
                    modal.start("Package", self.current_package_barcode);
                }
            }else{
                if(barcode == self.current_location_dest_barcode){
                    $('#current_product').hide("slide",{direction:'left', backgroundColor: "green"}, 400, function(){
                        self.move_package();
                        var $message = $(QWeb.render('info_package_barcode'));
                        $('#info_message').html($message)
                    });
                }else{
                    var modal = new instance.stock_irm.modal.barcode_error_modal();
                    modal.start("Location", self.current_location_dest_barcode);
                }
            }
        },
        move_package: function(){
            var self = this;

            self.session.rpc('/bandup/move_package', {
                package_id: self.package_list[0].package_id
            }).then(function(data){
                if(data.status == "ok"){
                    self.package_list.shift();
                    if(self.package_list.length > 0){
                        var current_package = self.package_list[0]
                        self.current_package_barcode = current_package.package_barcode;
                        self.current_location_dest_barcode = current_package.location_dest_barcode;
                        self.step = 'package';
                        self.display();
                    } else {
                        var modal = new instance.stock_irm.modal.confirm_bandup_wave_modal();
                        modal.start();
                        window.setTimeout(function(){
                            window.location.href = "/bandup";
                        }, 3000);
                    }

                }else{
                    console.log('error on moving package');
                }
            });


        }
    });

    instance.stock_irm.bandup_waves = bandup_waves;
})();
