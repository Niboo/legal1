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

    var rma_product_page = instance.stock_irm.widget.extend({
    	init: function (parent, id) {
            this._super('rma_product_page');
            var self = this;
            self.id = id;
            self.template = 'product_page';
            self.parent = parent;
            self.quantity = 0;
            self.barcodes = [];
            self.nb_already_printed = 0;
            self.quantity_to_print = 0;
            self.get_damage_reasons();
        },
        start: function(){
            this._super();
            var self = this;
            self.get_product();
        },
        get_product: function(){
            var self = this;
            self.session.rpc('/rma_screen/get_product', {
                id: self.id,
            }).then(function(data){
                if(data.status == 'ok'){
                    self.product = data.product;
                    self.barcodes = data.product.barcodes;

                    self.display();
                    self.parent.print_label(self.product.name, self.barcodes[0] , 1)
                    self.nb_already_printed += 1;
                } else {
                    self.display_error('Error', 'Could not get product information');
                }
            }, function(data){
                self.request_error(data);
            });
        },
        display: function(){
            var self = this;
            var po_move_line_by_picking = _.groupBy(self.parent.po_move_lines, function(po_move_line){
                return po_move_line.picking_name;
            });

            self.$elem = $(QWeb.render(self.template, {
                po_lines: po_move_line_by_picking,
                product: self.product,
                quantity: self.quantity,
                barcodes: self.barcodes,
                current_package_barcode: self.parent.current_package_barcode,
            }));

            $('#content').html(self.$elem);

            self.parent.get_the_box(self.product, self);

            // print the label the first time
            self.add_listener_on_valid_button();
            self.add_listener_on_quantity();
            self.add_listener_on_label_quantity();
            self.add_listener_on_print_button();
            self.add_listener_on_close_box();
            self.add_listener_on_move_to_damaged_button();
        },
        add_listener_on_valid_button: function(){
            var self = this;
            self.$elem.find('#ok_button').click(function(event){
                if(self.is_enough_label_printed()) {
                    $(':focus').blur();
                    var qty = self.$elem.find('#quantity input').get(0).value;
                    self.parent.add_product(self.product, parseInt(qty), self.parent.current_move_line);
                    self.destroy();
                }
            });
        },
        do_after_set_box: function(box, move_line){
            var self = this;
            self.$elem.find('#rack').html('<span class="glyphicon glyphicon-arrow-right"></span> <span> ' + move_line.picking_name + ' / ' + box + '</span>');
            self.add_listener_for_barcode();

            var move_line = self.parent.current_move_line;
            var qty_already_scanned = parseInt(move_line.quantity_already_scanned);
            var qty_to_add = parseInt(self.$elem.find('#quantity input').get(0).value);
            var qty_scanned = qty_already_scanned + qty_to_add;
            self.update_progress(move_line, qty_scanned);
        },

        update_progress: function(move_line, qty_scanned) {
            var self = this;
            var qty = move_line.quantity;
            var percentage = 100 / qty * qty_scanned;
            move_line.progress_done = percentage;
            self.$elem.find("#"+move_line.id).css({"width":move_line.progress_done+'%'});
        },

        add_listener_on_quantity: function(){
            var self = this;
            self.$elem.find('#quantity button').click(function(event){
                var qty = parseInt($('#quantity input').val());

                if($(event.currentTarget).attr('data-dir') == 'up'){
                    qty++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 0){
                        qty--;
                    }
                }

                var move_line = self.parent.current_move_line;
                var qty_scanned = move_line.quantity_already_scanned + qty;
                self.update_progress(move_line, qty_scanned);

                $('#quantity input').val(qty);

                if(qty-self.nb_already_printed >= 0){
                    self.quantity_to_print = qty-self.nb_already_printed
                    $('#quantity_to_print').val(self.quantity_to_print);
                }

                self.color_printed_labels(self.quantity_to_print);
                // force to lose focus to avoid adding +1 when scanning another product
                $(':focus').blur()
            });

            self.$elem.find('#quantity_to_print').keyup(function(event){
                $('#quantity_to_print').val(event.currentTarget.value);
                self.quantity_to_print = parseInt(event.currentTarget.value);
                self.color_printed_labels(self.quantity_to_print);
            })
        },
        add_listener_on_label_quantity: function(){
            var self = this;
            self.$elem.find('#label-quantity button').click(function(event){
                qty = parseInt($('#label-quantity input').val());

                if($(event.currentTarget).attr('data-dir') == 'up'){
                    self.quantity_to_print++;
                } else if ($(event.currentTarget).attr('data-dir') == 'dwn'){
                    if(qty > 0){
                        self.quantity_to_print--;
                    }
                }

                $('#quantity_to_print').val(self.quantity_to_print);
                $(':focus').blur()
            });
            self.$elem.off("keyup.quantity");
            self.$elem.on('keyup.quantity', '#input_quantity', function (event) {
                self.quantity_to_print = parseInt($('#input_quantity').val()) - self.nb_already_printed;
                if(self.quantity_to_print>0){
                    $('#quantity_to_print').val(self.quantity_to_print);
                }else{
                    $('#quantity_to_print').val(0);
                }
                self.color_printed_labels(self.quantity_to_print);
            })

        },
        add_listener_on_print_button: function(){
            var self = this;
            self.$elem.find('#label-printed button').click(function(event){
                if ($(event.currentTarget).attr('data-dir') == 'print'){
                    if (self.quantity_to_print > 0 ){
                        self.print_missing_labels();
                    }
                }
                $(':focus').blur()
            });
        },
        print_missing_labels: function(){
            var self = this;
            self.parent.print_label(self.product.name, self.barcodes[0], self.quantity_to_print);
            self.nb_already_printed += self.quantity_to_print;

            $('#already_printed_quantity').val(self.nb_already_printed);
            $('#quantity_to_print').val(0);
            self.quantity_to_print = 0;

            self.color_printed_labels(self.quantity_to_print);
        },
        color_printed_labels: function(){
            var self = this;
            var color = "green";
            if(self.quantity_to_print>0){
                color = "red"
            }

            $('#print_button').css({'color':color});
            $('#already_printed_quantity').css({'color':color});
        },
        add_listener_on_search_button: function(){
            var self = this;
            self.$nav.find('#search a').show();
            self.$nav.off('click.search');
            self.$nav.on('click.search', '#search a', function (event) {
                var qty = parseInt($('#quantity input').val());
                var product_image = $('#product_image').attr('src');

                var modal = new instance.stock_irm.modal.going_back_modal();
                modal.start(self, qty, product_image);
            })

        },
        add_listener_on_back_button: function(){
            var self = this;
            self.$nav.find('#back a').show();
            self.$nav.off('click.back');
            self.$nav.on('click.back', '#back a', function(event){
                var qty = parseInt($('#quantity input').val());
                var product_image = $('#product_image').attr('src');

                var modal = new instance.stock_irm.modal.going_back_modal();
                modal.start(self, qty, product_image);
            })
        },
        add_listener_on_confirm_button: function(){
            var self = this;
            self.$nav.off('click.confirm');
            self.$nav.on('click.confirm', '#confirm a', function(event){
                self.confirm_po_move();
            });
        },
        add_listener_on_close_box: function(){
            var self = this;
            self.$elem.off('click.closebox');
            self.$elem.on('click.closebox', '.close-box-icon', function(event){
                var box_barcode = $(event.currentTarget).attr('box-barcode');
                var modal = new instance.stock_irm.modal.close_box_modal();
                modal.start(self, box_barcode);
            })
        },
        add_listener_on_move_to_damaged_button: function(){
            var self = this;
            self.$elem.find('#mark_damaged_button').click(function(){
                var product_id = self.id;
                var modal = new instance.stock_irm.modal.damage_modal();
                modal.start(self, product_id, self.damage_reasons);
            })
        },
        get_damage_reasons: function () {
            var self = this;
            self.session.rpc('/rma_screen/get_damage_reasons')
                .then(function (data) {
                    if (data.status == 'ok') {
                        self.damage_reasons = data.damage_reasons;
                    } else {
                        self.display_error(data.error, data.message);
                    }
                }, function(data){
                    self.request_error(data);
                });
        },
        destroy: function(){
            this._super();
        },
        process_barcode: function(barcode) {
            var self = this;
            var qty = self.$elem.find('#quantity input').get(0).value;

            if(!_.contains(self.barcodes, barcode.replace(/[\s]*/g, ''))){
                if(self.is_enough_label_printed()){
                    //if we scanned another product, show warning
                    var qty = parseInt($('#quantity input').val());
                    var product_image = $('#product_image').attr('src');
                    var modal = new instance.stock_irm.modal.going_back_modal();
                    modal.start(self, qty, product_image);
                }
            } else {
                //if we scanned the same product, simply update the quantity and print the label
                qty++;

                var move_line = self.parent.current_move_line;
                var qty_scanned = move_line.quantity_already_scanned + qty;
                self.update_progress(move_line, qty_scanned);

                self.$elem.find('#quantity input').get(0).value = qty;

                // print the label each time we scan again
                self.parent.print_label(self.product.name, self.product.barcodes[0], 1)
                self.nb_already_printed += 1;
                $('#already_printed_quantity').val(self.nb_already_printed);
            }
        },
        is_enough_label_printed: function(){
            var self = this;
            if(self.quantity_to_print>0){
                var modal = new instance.stock_irm.modal.not_enough_label_modal(self)
                modal.start();
                return false;
            } else {
                return true;
            }
        },

        close_box: function(box_barcode){
            var self = this;
            self.parent.closed_boxes.push(box_barcode);
            var modal = new instance.stock_irm.modal.box_barcode_modal(self);
            modal.start();

            var $result = $(QWeb.render("rack_button", {
                name: self.parent.current_cart.name,
                index: self.parent.current_cart.box_index
            }));
            $('#rack').html($result);

            self.display();
        },
        close_box_if_no_more_product: function(product_id){
            var self = this;
            // this method is called when a PO line is validated.
            // It closes the current box if the current product is not needed anymore on the selected PO's
            // This way, extra product won't be added in the same box
            var po_line = $.grep(self.parent.purchase_order_lines, function(e){ return e.product_id == product_id && e.progress_done != 100.0; })[0];

            if(!po_line){
                self.parent.closed_boxes.push(self.parent.current_package_barcode);
            }
        },
    });

    instance.stock_irm.rma_product_page = rma_product_page;

})();
