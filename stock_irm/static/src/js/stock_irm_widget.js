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
    var last_key_time = 0;
    var barcode_string = "";
    instance.stock_irm = {};

    var stock_irm_widget= instance.Class.extend({
        init: function () {
            var self = this;
            self.session = new instance.Session();
            self.$nav = $('nav');
            self.$modal = $('#modalWindow');
            self.add_listeners();
        },
        add_listener_on_search_button: function(){
            var self = this;
            self.$nav.off('click.search');
            self.$nav.find('#search a').hide();
        },
        add_listener_on_back_button: function(){
            var self = this;
            self.$nav.off('click.back');
            self.$nav.find('#back a').hide();
        },
        add_listener_on_confirm_button: function(){
            var self = this;
            self.$nav.off('click.confirm');
            self.$nav.find('#confirm a').hide();
        },
        add_listener_for_barcode: function(){
            var self = this;
            var pressed = false;
            var chars = [];
            $(document).off('keypress.barcode');
            $(document).on('keypress.barcode', function(e) {
                chars.push(String.fromCharCode(e.which));
                if (pressed == false) {
                    setTimeout(function(){
                        if (chars.length >= 6) {
                            var barcode = chars.join("");
                            self.process_barcode(barcode)
                        }
                        chars = [];
                        pressed = false;
                    },500);
                }
                pressed = true;
            });
        },
        add_listener_on_user_button: function(){
            var self = this;
            var pressed = false;
            var chars = [];
            self.$nav.off('click.change-user');
            self.$nav.on('click.change-user', '#change-user a', function (event) {
                var $result = $(QWeb.render('change_user', {}));
                self.show_modal('Please enter your login information', $result, false);
                $(document).off('keypress.barcode');
                $(document).on('keypress.barcode', function(e) {
                    chars.push(String.fromCharCode(e.which));
                    if (pressed == false) {
                        setTimeout(function(){
                            if (chars.length >= 6) {
                                self.session.rpc('/inbound_screen/get_user', {
                                    'barcode': chars.join("").replace(/[\n\r]+/g, '')
                                }).then(function(data){
                                    if(data.status == "ok"){
                                        self.$modal.find('#login').val(data.login);
                                        self.$modal.find('#login-image').html("<div style=\"background-image:url('"+data.image+"');\"></div>");
                                        self.$modal.find('#login-image').show();
                                    }else{
                                        console.log("pas de user trouvé");
                                    }
                                });
                            }
                            chars = [];
                            pressed = false;
                        },500);
                    }
                    pressed = true;
                });

                self.$modal.find('#modal_changer_user_button').click(function(event){
                    event.preventDefault();
                    login = self.$modal.find('#login').val();
                    code = self.$modal.find('#login_code').val();

                    //TODO: really change the user connected to odoo. This only change the user being used on the page
                    window.location.href = "/inbound_screen/change_user?login="+login+"&login_code="+code;
                })
            });
        },
        process_barcode: function(barcode){
            // dummy method to process barcode
            console.log("Barcode Scanned: " + barcode);
        },
        add_listeners: function(){
            var self = this;
            self.add_listener_on_back_button();
            self.add_listener_on_search_button();
            self.add_listener_on_confirm_button();
            self.add_listener_for_barcode();
            self.add_listener_on_closing_modal();
            self.add_listener_on_user_button();
            self.add_listener_on_worklocation_button();
            if(!self.worklocation){
                self.get_worklocations();
            }
        },
        show_modal: function(title, content, block_modal){
            var self = this;
            if (typeof(block_modal)==='undefined') block_modal = true;
            $(document).off('keypress.barcode');
            self.$modal.find('.modal-title').html(title);
            self.$modal.find('.modal-body').html(content);
            if(block_modal){
                self.$modal.modal({
                    backdrop: 'static', // prevent from closing when clicking beside the modal
                    keyboard: false  // prevent closing when clicking on "escape"
                });
            }else{
                self.$modal.modal();
            }
        },
        add_listener_on_closing_modal: function(){
            var self = this;
            self.$modal.off('hide.bs.modal');
            self.$modal.on('hide.bs.modal', function() {
                self.$modal.find('.modal-title').empty();
                self.$modal.find('.modal-body').empty();
            })
        },
        destroy: function(){
        },
        add_listener_on_worklocation_button: function(){
            var self = this;

            self.$nav.off('click.change-worklocation');
            self.$nav.on('click.change-worklocation', '#change-worklocation a', function (event) {
                self.get_worklocations();
            });
        },
        get_worklocations: function(){
            var self = this;

            self.session.rpc('/inbound_screen/get_worklocations', {
            }).then(function(data){
                self.worklocations = data.worklocations;
                var $result = $(QWeb.render('worklocation_result', {
                    worklocations: self.worklocations,
                }));
                self.show_modal('Work Location Selection', $result);
                self.add_listener_on_worklocations();
            });
        },
        add_listener_on_worklocations: function(){
            var self = this;
            self.$modal.find('.modal-body .worklocation').click(function(event){
                event.preventDefault();
                var worklocation_id = $(event.currentTarget).attr('worklocation-id');
                var worklocation_name = $(event.currentTarget).attr('worklocation-name');
                self.worklocation = {
                    name: worklocation_name,
                    id: worklocation_id,
                }

                self.session.rpc('/inbound_screen/get_worklocation_printers', {
                    'location_id':self.worklocation.id}
                ).then(function(data){
                    self.printers = data.printers;
                });
                //TODO: keep the location between pages to avoid having the popup each time
                self.$modal.modal('hide');
                self.$nav.find('#change-worklocation').html('<a href="#"><span class="glyphicon glyphicon-cog"/> '+self.worklocation.name+'</a>');

            })
        },
    });

    instance.stock_irm.widget = stock_irm_widget
})();
