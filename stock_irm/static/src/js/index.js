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
    instance.index = {}

    var index_selector = instance.stock_irm.widget.extend({
        init: function () {
            this._super();
            var self = this;

            QWeb.add_template('/stock_irm/static/src/xml/index.xml', function(){
                self.start();
            });
            self.template = 'go_index';
        },
        start: function(){
            var self = this;
            self._super();
            self.session.rpc('/index/get_credentials', {}).then(function(data){
                if (data.status == 'ok'){
                    self.$elem = $(QWeb.render(self.template, {
                        is_wh_manager: data.is_wh_manager,
                        is_wh_user: data.is_wh_user,
                    }));
                    $('#content').html(self.$elem);
                } else {
                    self.display_error('Error', 'Could not retrieve credentials');
                }
            }, function(data){
                self.request_error(data);
            });
        },

    });
    instance.index.picking_selector = new index_selector();
})();
