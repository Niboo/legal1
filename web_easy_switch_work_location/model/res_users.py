# -*- encoding: utf-8 -*-
from openerp.osv.orm import Model


class res_users(Model):
    _inherit = 'res.users'

    # Custom Function Section
    def change_current_work_location(self, cr, uid, work_location_id, context=None):
        return self.write(cr, uid, uid, {'work_location_id': work_location_id})
