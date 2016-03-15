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

    var product_relation_abstract = instance.wln_website_offer.widget.extend({
    	init: function (product_relations, $container, level) {
            this._super();
            this.$parentElem = $container;
    		this.product_relations = product_relations;
    		this.simple_products = [];
    		this.exclusive_products = [];
    		this.mandatory_products = [];
    		this.mandatory_exclusive_products = [];
            this.started = false;
            this.is_included_in_pack = product_relations.is_included_in_pack;
            this.level = level;
            this.$elem = $(QWeb.render(this.template, this.product_relations));
            this.$qty = this.$elem.find('//qty');
            if (parseInt(this.$qty.val()) < 1) {this.$qty.hide()} else {this.$qty.show()}

            this.SimpleWidget = instance.wln_website_offer.product_relation_widget.simple;
            this.ExclusiveWidget = instance.wln_website_offer.product_relation_widget.exclusive;
            this.MandatoryWidget = instance.wln_website_offer.product_relation_widget.mandatory;
            this.MandatoryExclusiveWidget = instance.wln_website_offer.product_relation_widget.mandatory_exclusive;

            this.loadProducts();
            this.children = this.getChildren(this);
        },
        loadProducts: function() {
            for (var simple in this.product_relations.simple) {
    			var relations = this.product_relations.simple[simple];
    			this.simple_products.push(new this.SimpleWidget(relations, this.$elem, this.level+1));
    		}
    		for (var exclusive in this.product_relations.simple_exclusive) {
    			var relations = this.product_relations.simple_exclusive[exclusive];
    			this.exclusive_products.push(new this.ExclusiveWidget(relations, this.$elem, this.level+1));
    		}
    		for (var mandatory in this.product_relations.mandatory) {
    			var relations = this.product_relations.mandatory[mandatory];
    			this.mandatory_products.push(new this.MandatoryWidget(relations, this.$elem, this.level+1));
    		}
    		for (var mandatory_exclusive in this.product_relations.mandatory_exclusive) {
    			var relations = this.product_relations.mandatory_exclusive[mandatory_exclusive];
    			this.mandatory_exclusive_products.push(new this.MandatoryExclusiveWidget(relations, this.$elem, this.level+1));
    		}
        },
        start: function () {
            this.started = true;
            this.display();
        },
        stop: function() {
            if (this.started) {
                this.started = false;
                this.stopChilds();
                this.$elem.remove();
            }
        },
        getChildren: function(relations) {
            var childs = [];
            for (var mandatory in relations.mandatory_products) {
            	childs.push(relations.mandatory_products[mandatory]);
            }
            for (var exclusive in relations.mandatory_exclusive_products) {
                childs.push(relations.mandatory_exclusive_products[exclusive]);
            }
            for (var simple in relations.simple_products) {
                childs.push(relations.simple_products[simple]);
            }
            for (var exclusive in relations.exclusive_products) {
                childs.push(relations.exclusive_products[exclusive]);
            }
            return childs;
        },
        computeQty: function (parent_qty) {
            var self = this;
            if (self.product_relations.based_on == 'pr'){
                var old_quantity = self.quantity;
                self.quantity = parent_qty + self.product_relations.offset;
                if(old_quantity < 1 && self.quantity >= 1){
                    self.$qty.show();
                } else {
                    if(self.quantity < 1){
                        self.$qty.hide();
                    }
                }
                self.$qty.val(self.quantity);
                self.children.forEach(function(element, index, array){
                    element.computeQty(self.quantity);
                });
            }
        },
        startChilds: function () {
            var self = this;
            this.children.forEach(function(element, index, array){
                element.computeQty(self.quantity);
                element.start();
            });
        },
        stopChilds: function () {
            this.children.forEach(function(element, index, array){
               element.stop();
            });
        },
        getIdsQties: function() {
            var ids = [this.id, this.quantity, this.is_included_in_pack];
            if(this.tid_widget !== undefined) {
                ids.push(this.tid_widget.getTids());
            } else {
                ids.push(undefined);
            }
            ids = [ids];
            for (var child in this.children) {
                ids = ids.concat(this.children[child].getIdsQties());
            }
            return ids;
        },
        display: function () {
            this.$parentElem.append(this.$elem);
        },
    });
    instance.wln_website_offer.product_relation_widget.abstract = product_relation_abstract;

    var product_relation_master = instance.wln_website_offer.product_relation_widget.abstract.extend({
    	init: function (product_relations, $container, level) {
            this.id = product_relations.id;
            this.quantity = product_relations.quantity;
            this.template = 'master_product';
            this._super(product_relations, $container, level);
            this.start();
        },
        start: function () {
            this.started = true;
            var header = $("//product_relation_modal .modal-header");
            render = QWeb.render("master_header", this.product_relations);
            header.html(render);
            this.display();
            if (this.children.length > 0){
                this.$elem.append("<h4>Product relations</h4>");
                this.startChilds();
            }
            if(this.product_relations.is_required_tid){
                var $tid_dialog_button = header.find('.tid_dialog_button');
                this.tid_widget = new instance.wln_website_offer.tid_widget($tid_dialog_button, true);
                var self = this;
                $tid_dialog_button.click(function(){
                    self.tid_widget.display(self.quantity);
                });
            }
        },
    });
    instance.wln_website_offer.product_relation_widget.master = product_relation_master;

    var product_relation_simple = instance.wln_website_offer.product_relation_widget.abstract.extend({
    	init: function (product_relations, $container, level) {
            this.id = product_relations.id;
            this.quantity = product_relations.quantity;
            this.template = 'simple_product';
            this.selected = false;
            product_relations['level'] = level;

            this._super(product_relations, $container, level);
    	},
        start: function () {
            this._super();
            if (this.product_relations.default) {
                this.startChilds();
                this.selected = true;
            }
            if(this.product_relations.is_required_tid){
                var id = this.product_relations.id;
                this.tid_widget = new instance.wln_website_offer.tid_widget(this.$elem.find('[product_id=' + id + ']'), this.selected);
            }
            this.initListeners();
        },
        initListeners: function() {
            var self = this;
            self.$elem.find('input[value="' + self.id + '"]').change(function(data){
                var checked = $(this).is(':checked');
                if (checked) {
                    self.startChilds();
                } else {
                    self.stopChilds();
                }
                if (self.product_relations.is_required_tid) {
                    self.tid_widget.toggleTidButton(checked);
                }
                self.selected = checked;
            });
            self.$elem.find('//qty').change(function (data) {
                if (self.product_relations.max_qty){
                    if (parseInt(data.currentTarget.value) > self.product_relations.max_qty){
                        self.$qty.val(self.product_relations.max_qty);
                        data.currentTarget.value = self.product_relations.max_qty;
                    }
                }
                
                self.quantity = parseInt(data.currentTarget.value);
                self.children.forEach(function(element, index, array){
                    element.computeQty(self.quantity);
                });
                if (self.product_relations.is_required_tid) {
                    self.tid_widget.resetTids();
                }
            });
            if (self.product_relations.is_required_tid) {
                self.$elem.find('[product_id=' + self.id + ']').click(function () {
                    self.tid_widget.display(self.quantity);
                });
            }
        },
        getIdsQties: function() {
            var self = this;
            var ids = []

            if(self.selected) {
                for (var child in this.children) {
                    ids = ids.concat(this.children[child].getIdsQties());
                }
                var ids_tmp = [self.id, self.quantity, self.is_included_in_pack];
                if (self.tid_widget !== undefined) {
                    ids_tmp.push(self.tid_widget.getTids());
                } else {
                    ids_tmp.push(undefined);
                }
                ids.push(ids_tmp);
            }
            return ids;
        },
    });
    instance.wln_website_offer.product_relation_widget.simple = product_relation_simple;

    var product_relation_mandatory = instance.wln_website_offer.product_relation_widget.abstract.extend({
    	init: function (product_relations, $container, level) {
            this.id = product_relations.id;
            this.quantity = product_relations.quantity;
    		this.template = 'mandatory_product';
            product_relations['level'] = level;
            this._super(product_relations, $container, level);
    	},
        start: function (){
            this._super();
            this.startChilds();
            if(this.product_relations.is_required_tid){
                var id = this.product_relations.id;
                this.tid_widget = new instance.wln_website_offer.tid_widget(this.$elem.find('[product_id=' + id + ']'), true);
            }
            this.initListeners();
        },
        initListeners: function() {
            var self = this;
            self.$elem.find('//qty').change(function(data){
                if (self.product_relations.max_qty){
                    if (parseInt(data.currentTarget.value) > self.product_relations.max_qty){
                        self.$qty.val(self.product_relations.max_qty);
                        data.currentTarget.value = self.product_relations.max_qty;
                    }
                }

                self.quantity = parseInt(data.currentTarget.value);
                self.children.forEach(function(element, index, array){
                    element.computeQty(self.quantity);
                });
                if(self.product_relations.is_required_tid){
                    self.tid_widget.resetTids();
                }
            });
            if(self.product_relations.is_required_tid){
                self.$elem.find('[product_id=' + self.id + ']').click(function(){
                    self.tid_widget.display(self.quantity);
                });
            }
        },
    });
    instance.wln_website_offer.product_relation_widget.mandatory = product_relation_mandatory;

    var product_relation_exclusive = instance.wln_website_offer.product_relation_widget.abstract.extend({
    	init: function (product_relations, $container, level) {
            this.childGroup = {}
            this.selected = false;
            if (typeof this.template == 'undefined') {
                this.template = "exclusive_product";
            };
            this.quantity = 1;
            this.id = Math.random().toString(36).substr(2);
            product_relations = {'group_id': this.id, 'relations': product_relations, 'level': level};
            this._super(product_relations, $container, level);
    	},
        loadProducts: function() {
            var self = this;

            for (var index in self.product_relations.relations){
    			var product = self.product_relations.relations[index];
                var relations = {}

                relations.simple_products = [];
    		    relations.exclusive_products = [];
    		    relations.mandatory_products = [];
    		    relations.mandatory_exclusive_products = [];
                relations.tid_required = product.is_required_tid;
                if(product.is_required_tid){
                    var $button = self.$elem.find('[product_id=' + product.id + ']');
                    relations.tid_widget = new instance.wln_website_offer.tid_widget($button, product.default);
                }
                if(product.quantity < 1){
                    self.$elem.find('.qty//'+product.id).hide();
                } else {
                    self.$elem.find('.qty//'+product.id).show();
                }
                self.childGroup[product.id] = relations;

    			for (var simple in product.simple) {
	    			var simple_relations = product.simple[simple];
	    			relations.simple_products.push(new this.SimpleWidget(simple_relations, this.$elem.find('//product_relation_'+product.id), this.level+1));
	    		};
	    		for (var exclusive in product.simple_exclusive) {
	    			var exclusive_relations = product.simple_exclusive[exclusive];
	    			relations.exclusive_products.push(new this.ExclusiveWidget(exclusive_relations, this.$elem.find('//product_relation_'+product.id), this.level+1));
	    		};
	    		for (var mandatory in product.mandatory) {
	    			var mandatory_relations = product.mandatory[mandatory];
	    			relations.mandatory_products.push(new this.MandatoryWidget(mandatory_relations, this.$elem.find('//product_relation_'+product.id), this.level+1));
	    		};
	    		for (var mandatory_exclusive in product.mandatory_exclusive) {
	    			var mandatory_exclusive_relations = product.mandatory_exclusive[mandatory_exclusive];
	    			relations.mandatory_exclusive_products.push(new this.MandatoryExclusiveWidget(mandatory_exclusive_relations, this.$elem.find('//product_relation_'+product.id), this.level+1));
	    		};

                if (product.default){
                    self.selected = product.id;
                }
    		};
        },
        computeQty: function (parent_qty) {
            var self = this;
            for (var index in self.product_relations.relations){
                var product = self.product_relations.relations[index];
                if (product.based_on == 'pr'){
                    product.quantity = parent_qty + product.offset;
                    if (product.id === parseInt(self.selected)){
                        self.quantity = parent_qty + product.offset;
                        var relations = self.childGroup[product.id];
                        self.getChildren(relations).forEach(function(element, index, array){
                            element.computeQty(self.quantity);
                        });
                    }
                    var $qty = self.$elem.find('.qty//'+product.id);
                    $qty.val(product.quantity);
                    if(product.quantity < 1){
                        $qty.hide();
                    } else {
                        $qty.show();
                    }
                }
            }
        },
    	start: function () {
            var self = this;
            self._super();
            self.initListeners();
            self.startChilds();
        },
        initListeners: function() {
            var self = this;
            self.$elem.find('input[name="exclusive_' + self.id + '"]').change(function(data){
                self.stopChilds();
                self.selected = $(this).val();
                var qty = self.$elem.find('.qty//'+self.selected);
                for(var key in self.childGroup){
                    if(self.childGroup[key].tid_required){
                        self.childGroup[key].tid_widget.toggleTidButton(key == self.selected);
                    }
                }
                if (qty.length === 1) {
                    self.quantity = parseInt(qty.val());
                }
                self.startChilds();
            });
            self.$elem.find('.qty').change(function(data){
                for (var index in self.product_relations.relations){
                    var product = self.product_relations.relations[index];
                    if (parseInt(data.currentTarget.id) === product.id) {
                        if (product.max_qty){
                            if (parseInt(data.currentTarget.value) > product.max_qty){
                                self.$elem.find('.qty//'+product.id).val(product.max_qty);
                                data.currentTarget.value = product.max_qty;
                            }
                        }
                    }
                }

                if (parseInt(data.currentTarget.id) === parseInt(self.selected)) {
                    self.quantity = parseInt(data.currentTarget.value);
                    self.getChildren(self.childGroup[self.selected]).forEach(function(element, index, array){
                        element.computeQty(self.quantity);
                    });
                    if(self.childGroup[self.selected].is_required_tid){
                        self.childGroup[self.selected].tid_widget.resetTids();
                    }
                }
            });
            self.$elem.find('.tid_dialog_button').click(function(data){
                if (parseInt($(data.currentTarget).attr('product_id')) === parseInt(self.selected)) {
                    self.childGroup[self.selected].tid_widget.display(self.quantity);
                }
            });
        },
        stopChilds: function(){
            var self = this;
            for (var product_id in self.childGroup) {
                var relations = self.childGroup[product_id];
                self.getChildren(relations).forEach(function(element, index, array){
                    element.stop();
                });
            }
        },
        startChilds: function (){
            var self = this;
            if (self.selected && self.selected != '0') {
                var relations = self.childGroup[this.selected];
                self.getChildren(relations).forEach(function(element, index, array){
                    element.computeQty(self.quantity);
                    element.start();
                });
            }
        },
        getIdsQties: function() {
            var self = this;
            var ids = []
            if (self.selected && self.selected != '0') {
                var relations = self.childGroup[self.selected];
                var children = self.getChildren(relations)

                for (var child in children) {
                    ids = ids.concat(children[child].getIdsQties());
                }

                var is_included_in_pack = false;
                for (var index in self.product_relations.relations){
                    var product = self.product_relations.relations[index];
                    if (product.id == parseInt(self.selected))
                    {
                        is_included_in_pack = product.is_included_in_pack;
                    }
                }

                var ids_tmp = [parseInt(self.selected), self.quantity, is_included_in_pack];
                if (self.childGroup[self.selected].tid_widget !== undefined) {
                    ids_tmp.push(self.childGroup[self.selected].tid_widget.getTids());
                } else {
                    ids_tmp.push(undefined);
                }
                ids.push(ids_tmp);
            }
            return ids;
        },
    });
    instance.wln_website_offer.product_relation_widget.exclusive = product_relation_exclusive;

    var product_relation_mandatory_exclusive = instance.wln_website_offer.product_relation_widget.exclusive.extend({
    	init: function (product_relations, $container, level) {
    		this.template = "mandatory_exclusive_product";
            this._super(product_relations, $container, level);
    	},
    });
    instance.wln_website_offer.product_relation_widget.mandatory_exclusive = product_relation_mandatory_exclusive;
})();
