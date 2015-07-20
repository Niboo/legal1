openerp.im_chat_group = function(){

    openerp.im_chat.ConversationManager.include({
        notifyMe: function() {
            if (!Notification) {
                alert('Please us a modern version of Chrome, Firefox, Opera or Firefox.');
                return;
            }
            if (Notification.permission !== "granted")
                Notification.requestPermission();
            var company = this.session.company_id;
            var notification = new Notification('Incoming Chat', {
                icon: "https://www.odoo.com/logo.png",
                body: 'You have Conversation update',
            });
            notification.onclick = function(x) { window.focus(); };
        },
        window_beep: function() {
            this._super.apply(this, arguments);
            this.notifyMe();
        }
    });
    openerp.im_chat.InstantMessaging.include({
        start: function(){
            this._super.apply(this, arguments);
            this.group_users = {};
            this.group_data = []
            self = this;
            var group_model = new openerp.web.Model("mail.group");
            group_model.call('search_read', [ [['is_chat', '=', true]], ['name']]).pipe(function(results) {
                _.each(results, function(result) {
                    var user = {
                        "id" : 'g_id_'+result['id'],
                        "name": result['name'],
                        "im_status": 'online',
                        "image_url":  openerp.session.url('/web/binary/image', {model:'mail.group', field: 'image', id: result['id']})
                    };
                    self.group_data.push(user);
                    var widget = new openerp.im_chat.UserWidget(self, user);
                    widget.appendTo(self.$(".oe_im_users"));
                    //widget.$el.addClass('odoo_support_contact');
                    widget.on("activate_user", self, self.activate_user);
                });
            });
        },
        /*search_users_status11: function(e) {
            self = this;
            this._super.apply(this, arguments).then(function(res){
                _.each(self.group_data, function(user) {
                    var widget = new openerp.im_chat.UserWidget(self, user);
                    widget.appendTo(self.$(".oe_im_users"));
                    //widget.$el.addClass('odoo_support_contact');
                    self.group_users[user['id']] = widget;
                    widget.on("activate_user", self, self.activate_user);
                    //self.widgets[user['id']] = widget;
                });
                return res; 
            });
        },*/
    });
};
