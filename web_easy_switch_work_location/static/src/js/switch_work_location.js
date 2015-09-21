openerp.web_easy_switch_work_location = function (instance) {

    /***************************************************************************
    Create an new 'SwitchLocationWidget' widget that allow users to switch
    from a company to another more easily.
    ***************************************************************************/
    instance.web.SwitchLocationWidget = instance.web.Widget.extend({

        template:'web_easy_switch_work_location.SwitchLocationWidget',

        /***********************************************************************
        Overload section
        ***********************************************************************/

        /**
         * Overload 'init' function to initialize the values of the widget.
         */
        init: function(parent){
            this._super(parent);
            this.work_locations = [];
            this.current_work_location_id = 0;
            this.current_work_location_name = '';
        },

        /**
         * Overload 'start' function to load datas from DB.
         */
        start: function () {
            this._super();
            this._load_data();
        },

        /**
         * Overload 'renderElement' function to set events on company items.
         */
        renderElement: function() {
            var self = this;
            this._super();
            if (this.work_locations.length === 1) {
                this.$el.hide();
            }
            else{
                this.$el.show();
                this.$el.find('.easy_switch_work_location_item').on('click', function(ev) {
                    var work_location_id = $(ev.target).data("work-location-id");


                    if (work_location_id != self.current_work_location_id){
                        var func = '/web_easy_switch_work_location/switch/change_current_work_location';
                        var param = {'work_location_id': work_location_id}
                        self.rpc(func, param).done(function(res) {
                            window.location.reload()
                        });
                    }
                });
            }
        },


        /***********************************************************************
        Custom section
        ***********************************************************************/

        /**
         * helper function to load data from the server
         */
        _fetch: function(model, fields, domain, ctx){
            return new instance.web.Model(model).query(fields).filter(domain).context(ctx).all();
        },

        /**
         * - Load work locations;
         * - Launch the rendering of the current widget;
         */
        _load_data: function(){
            var self = this;
            this._fetch('res.users',['work_location_id'],[['id','=',this.session.uid]]).then(function(res_users){
                self.current_work_location_id = res_users[0].work_location_id[0];
                self.current_work_location_name = res_users[0].work_location_id[1];
                new instance.web.Model('work_location').call('name_search',{context:{'user_preference':'True'}}).then(function(res){
                    var res_work_location = res;
                    for ( var i=0; i < res_work_location.length; i++) {
                        var logo_state;
                        if (res_work_location[i][0] == self.current_work_location_id){
                            logo_state = '/web_easy_switch_work_location/static/description/selection-on.png';
                        }
                        else {
                            logo_state = '/web_easy_switch_work_location/static/description/selection-off.png';
                        }
                        self.work_locations.push({
                            id: res_work_location[i][0],
                            name: res_work_location[i][1],
                            logo_state: logo_state
                        });
                    }
                    self.renderElement();
                });
            });
        },

    });

    /***************************************************************************
    Extend 'UserMenu' Widget to insert a 'SwitchLocationWidget' widget.
    ***************************************************************************/
    instance.web.UserMenu =  instance.web.UserMenu.extend({

        init: function(parent) {
            this._super(parent);
            var switch_button = new instance.web.SwitchLocationWidget();
            switch_button.appendTo(instance.webclient.$el.find('.oe_systray'));
        }

    });

};

