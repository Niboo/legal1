from openerp.osv import osv, fields
from openerp import SUPERUSER_ID

class mail_message(osv.osv):
    _inherit = "mail.message"

    def _company_id(self, cr, uid, ids, name, args, context={}):
        result = dict.fromkeys(ids, False)
        for message in self.browse(cr, uid, ids, context=context):
            if hasattr(self.pool.get(message.model),'browse'):
                message_obj = self.pool.get(message.model).browse(cr, SUPERUSER_ID, message.res_id, context=context)
                if hasattr(message_obj,'company_id'):
                    result[message.id] = message_obj.company_id.id
        return result

    _columns = {
        'xx_company_id': fields.function(_company_id, method=True, string='Company',type="many2one",obj="res.company",store=True),
    }
