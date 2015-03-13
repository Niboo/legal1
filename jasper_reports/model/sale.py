from openerp.osv import orm, osv, fields
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):

    _inherit = "sale.order"

    def print_quotation(self, cr, uid, ids, context=None):
        result = super(sale_order, self).print_quotation(cr, uid, ids, context=context)
        
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        order = self.pool.get('sale.order').browse(cr, uid, ids[0], context=context)

        if order.state in ('draft', 'sent'):
            return self.pool.get('res.partner').get_report(cr, uid, [order.partner_id.id], 'quotation', result.get('datas'), context=context)
        else:
            return self.pool.get('res.partner').get_report(cr, uid, [order.partner_id.id], 'sale_order', result.get('datas'), context=context)

    def action_quotation_send(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        order = self.pool.get('sale.order').browse(cr, uid, ids[0], context=context)
        
        ir_model_data = self.pool.get('ir.model.data')

        try:
            if order.state in ('draft', 'sent'):
                template_id = self.pool.get('res.partner').get_email_template(cr, uid, [order.partner_id.id], 'quotation', context=context)
            else:
                template_id = self.pool.get('res.partner').get_email_template(cr, uid, [order.partner_id.id], 'sale_order', context=context)
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        ctx.update({
            'default_model': 'sale.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }