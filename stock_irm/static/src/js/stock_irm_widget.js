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
    instance.stock_irm.modal = {};

    var inbound_modal = instance.Class.extend({
        init: function (caller) {
            var self = this;
            self.session = new instance.Session();
            self.$modal = $('#modalWindow');
            self.caller = caller;
            self.title = '';
            self.$body = '';
            self.$footer = '';
        },
        start: function () {
            var self = this;
            self.show_modal();
        },
        show_modal: function(){
            var self = this;

            if (typeof(footer)==='undefined') footer = '';
            if (typeof(self.block_modal)==='undefined') self.block_modal = false;

            if (self.block_modal){
                self.$modal = $('#blockedModalWindow');
            }else{
                self.$modal = $('#modalWindow');
            }
            $(document).off('keypress.barcode');
            self.$modal.find('.modal-title').html(self.title);
            self.$modal.find('.modal-body').html(self.$body);
            self.$modal.find('.modal-footer').html(self.$footer);
            if(self.block_modal){
                self.$modal.modal({
                    backdrop: 'static', // prevent from closing when clicking beside the modal
                    keyboard: false  // prevent closing when clicking on "escape"
                });
            }else{
                self.$modal.modal();
            }

        },
    });

    instance.stock_irm.modal.widget = inbound_modal

    var exception_modal = instance.stock_irm.modal.widget.extend({
        init: function () {
            var self = this;
            self.body_template = 'exception_modal';
            self.title = 'Print Error';
            this._super();
        },
        start: function (error, message) {
            var self = this;
            self.$body = $(QWeb.render(self.body_template, {
                'error': error,
                'message': message,
            }));
            this._super();
        },
    });

    instance.stock_irm.modal.exception_modal = exception_modal;
        
    var change_user_modal = inbound_modal.extend({
        init: function () {
            var self = this;
            self.body_template = 'change_user';
            self.footer_template = 'change_user_footer';
            self.title = 'Please enter your login information';
            this._super();
        },
        start: function () {
            var self = this;
            self.$body = $(QWeb.render(self.body_template));
            self.$footer = $(QWeb.render(self.footer_template));
            this._super();
            var pressed = false;
            var chars = [];
            $(document).off('keypress.barcodeuser');
            $(document).on('keypress.barcodeuser', function(e) {
                chars.push(String.fromCharCode(e.which));
                if (pressed == false) {
                    setTimeout(function(){
                        if (chars.length >= 6) {
                            self.session.rpc('/inbound_screen/get_user', {
                                'barcode': chars.join("").replace(/[\s]*/g, '')
                            }).then(function(data){
                                if(data.status == "ok"){
                                    self.$modal.find('#login').val(data.login);
                                    self.$modal.find('#login-image').html("<img src='"+data.image+"'/>");
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
                var login = self.$modal.find('#login').val();
                var password = self.$modal.find('#password').val();

                var data = {'login':login,'password':password}
                $.post("/inbound_screen/change_user", data, function(data, status){
                    location.reload();
                })
            });
            self.$modal.on('hidden.bs.modal', function () {
                $(document).off('keypress.barcodeuser');
            });
        },
    });

    instance.stock_irm.modal.change_user_modal = change_user_modal;

    var worklocation_modal = instance.stock_irm.modal.widget.extend({
        init: function (caller) {
            var self = this;
            self.body_template = 'worklocation_result';
            self.title = 'Work Location Selection';
            this._super(caller);
        },
        start: function (worklocations) {
            var self = this;
            self.$body = $(QWeb.render(self.body_template, {
                worklocations: worklocations,
            }));
            this._super();
            self.add_listener_on_worklocations();
        },
        add_listener_on_worklocations: function(){
            var self = this;
            self.$modal.find('.modal-body .worklocation').click(function(event){
                event.preventDefault();
                var worklocation_id = $(event.currentTarget).attr('worklocation-id');
                var worklocation_name = $(event.currentTarget).attr('worklocation-name');
                $('#change-worklocation').attr('data-id', worklocation_id);

                self.session.rpc('/inbound_screen/get_worklocation_printers', {
                    'location_id':worklocation_id,
                }).then(function(data){
                    self.caller.worklocation = {
                        name: worklocation_name,
                        id: worklocation_id,
                    };
                    self.caller.set_worklocation();
                });
                self.$modal.modal('hide');
            })
        },
    });

    instance.stock_irm.modal.worklocation_modal = worklocation_modal;

    var stock_irm_widget = instance.Class.extend({
        init: function (class_name) {
            var self = this;
            self.session = new instance.Session();
            self.$nav = $('nav');
            self.class_name = class_name;
        },
        start: function(){
            var self = this;
            self.add_listeners();
        },
        add_listener_on_search_button: function(){
            var self = this;
            self.$nav.off('click.search');
        },
        add_listener_on_back_button: function(){
            var self = this;
            self.$nav.off('click.back');
        },
        add_listener_on_confirm_button: function(){
            var self = this;
            self.$nav.off('click.confirm');
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
                    },100);
                }
                pressed = true;
            });
        },
        add_listener_on_user_button: function(){
            var self = this;

            self.$nav.off('click.change-user');
            self.$nav.on('click.change-user', '#change-user a', function (event) {
                var modal = new change_user_modal();
                modal.start()

            });
        },
        add_listener_on_fullscreen_button: function() {
            var self = this;

            $('#fullscreen').click(function() {
                self.toggleFullScreen(document.documentElement);
            });
        },
        add_listener_on_print_pickings_button: function() {
            var self = this;

            $('#print-pickings').click(function() {
                self.session.rpc('/print_pickings', {
                    'wave_id' : self.wave_id,
                }).then(function(data) {
                    if(data.status == 'ok'){
                        console.log('Print all pickings: Success')
                    } else {
                        console.log('Error while trying to print all pickings.')
                        var modal = new exception_modal();
                        modal.start(data.error, data.message);
                    }
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
            self.add_listener_on_user_button();
            self.add_listener_on_worklocation_button();
            self.add_listener_on_print_pickings_button();
            self.add_listener_on_fullscreen_button();
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
                var modal = new worklocation_modal(self);
                modal.start(self.worklocations);
            });
        },
        toggleFullScreen: function(element) {
            if ((document.fullScreenElement && document.fullScreenElement !== null) ||
                (!document.mozFullScreen && !document.webkitIsFullScreen)) {
                if (document.documentElement.requestFullScreen) {
                    document.documentElement.requestFullScreen();
                } else if (document.documentElement.mozRequestFullScreen) {
                    document.documentElement.mozRequestFullScreen();
                } else if (document.documentElement.webkitRequestFullScreen) {
                    document.documentElement.webkitRequestFullScreen(Element.ALLOW_KEYBOARD_INPUT);
                }
            } else {
                if (document.cancelFullScreen) {
                    document.cancelFullScreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.webkitCancelFullScreen) {
                    document.webkitCancelFullScreen();
                }
            }
        },
        set_worklocation: function(data) {
            var self = this;
            self.$nav.find('#change-worklocation').html('<a href="#"><span class="glyphicon glyphicon-cog"/> '+self.worklocation.name+'</a>');
            self.session.rpc('/inbound_screen/switch_worklocation', {
                'new_work_location_id': self.worklocation.id,
            }).then(function(data){
                self.printer_ip = data.printer_ip;
            });
        },
    });

    instance.stock_irm.widget = stock_irm_widget
})();
