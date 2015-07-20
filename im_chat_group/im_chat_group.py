import openerp
from openerp.http import request
from openerp.osv import osv, fields

class mail_group(osv.Model):
    _inherit = 'mail.group'
    
    _columns = {
        'is_chat': fields.boolean('Is Available for chat')
    }
    
class im_chat_session(osv.Model):   
    _inherit = 'im_chat.session'
    _columns = {
        'mail_group_id': fields.many2one('mail.group', 'Mail Group'),
    }
    def session_get(self, cr, uid, user_to, context=None):
        if isinstance(user_to, (str, unicode)) and user_to.startswith('g_id_'):
            group_id = int(user_to.replace("g_id_", ""))
            group_pool = self.pool.get('mail.group')
            session_id = self.search(cr, uid, [('mail_group_id', '=', group_id)])
            group_data = group_pool.read(cr, uid, group_id, ['message_follower_ids'])
            user_ids = self.pool.get('res.users').search(
                cr, uid, [('partner_id', 'in', group_data['message_follower_ids'])])
            if not session_id:
                session_id = self.create(cr, uid, {'user_ids': [(6,0, user_ids)], 'mail_group_id': group_id}, context=context)
            else:
                self.write(cr, uid, session_id, {'user_ids': [(6,0, user_ids)]}, context=context)
                session_id = session_id[0]
            return self.session_info(cr, uid, [session_id], context=context)
        else:
            return super(im_chat_session, self).session_get(cr, uid, user_to, context=context)       
class im_chat_message(osv.Model):
    """ Sessions messsages type can be 'message' or 'meta'.
        For anonymous message, the from_id is False.
        Messages are sent to a session not to users.
    """
    _inherit = 'im_chat.message'     
    
    _columns = {
        'user_ids': fields.related('to_id', 'user_ids', type="many2many", relation="res.users"),
    } 
