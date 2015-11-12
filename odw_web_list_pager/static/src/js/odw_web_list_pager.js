openerp.odw_web_list_pager = function(instance){
    _t = instance.web._t;

    instance.web.ListView.include({
        init: function() {
            /* Reinjecting the pager options with an additional option for 20 items.
               This won't change the default, which is as per customer requirement */
            this._super.apply(this, arguments);
            var self = this;
            this.on('list_view_loaded', this, function() {
                this.$pager.find('.oe_list_pager_state').click(function (e) {
                    e.stopPropagation();
                    var $this = $(this);

                    var $select = $('<select>')
                        .appendTo($this.empty())
                        .click(function (e) {e.stopPropagation();})
                        .append('<option value="20">20</option>' +
                                '<option value="80">80</option>' +
                                '<option value="200">200</option>' +
                                '<option value="500">500</option>' +
                                '<option value="2000">2000</option>' +
                                '<option value="NaN">' + _t("Unlimited") + '</option>')
                        .change(function () {
                            var val = parseInt($select.val(), 10);
                            self._limit = (isNaN(val) ? null : val);
                            self.page = 0;
                            self.reload_content();
                        }).blur(function() {
                            $(this).trigger('change');
                        })
                        .val(self._limit || 'NaN');
                });
            });
        },
    });
}
