from openerp.osv import orm, osv, fields
from openerp.tools.translate import _

class res_partner(osv.osv):
    
    _inherit = 'res.partner'

    def get_report(self, cr, uid, id, document_type, datas, context=None):

        assert len(id) == 1, 'This option should only be used for a single id at a time.'

        ids = self.pool.get('xx.partner.document.layout').search(cr, uid, [('document_type','=',document_type),('partner_id','in',id)])
        document_options = False
        if ids:
            document_layout = self.pool.get('xx.partner.document.layout').browse(cr, uid, ids[0])
            document_options = {'jasper_report': document_layout.jasper_report.report_name,
                                'nb_of_copies': document_layout.nb_of_copies,}
        else:
            ids = self.pool.get('xx.document.layout').search(cr, uid, [('document_type','=',document_type),('company_id','=',self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id)])
            if ids:
                document_layout = self.pool.get('xx.document.layout').browse(cr, uid, ids[0])
                document_options = {'jasper_report': document_layout.jasper_report.report_name,
                                    'nb_of_copies': document_layout.nb_of_copies,}

        if not document_options:
            raise osv.except_osv('Warning', _('Document Layout not specified for Document Type "%s" !') % (document_type))
            
        datas.update({'nb_of_copies':document_options.get('nb_of_copies')})
        return {'type': 'ir.actions.report.xml', 'report_name': document_options.get('jasper_report'), 'datas': datas, 'nodestroy': True}

    def get_email_template(self, cr, uid, id, document_type, context=None):

        assert len(id) == 1, 'This option should only be used for a single id at a time.'

        ids = self.pool.get('xx.partner.email.layout').search(cr, uid, [('document_type','=',document_type),('partner_id','=',id)])
        email_template = False
        if ids:
            email_layout = self.pool.get('xx.partner.email.layout').browse(cr, uid, ids[0])
            email_template = email_layout.email_template.id
        else:
            ids = self.pool.get('xx.email.layout').search(cr, uid, [('document_type','=',document_type),('company_id','=',self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id)])
            if ids:
                email_layout = self.pool.get('xx.email.layout').browse(cr, uid, ids[0])
                email_template = email_layout.email_template.id

        return email_template

    _columns = {
        'xx_partner_document_layouts': fields.one2many('xx.partner.document.layout','partner_id','Print Layouts'),
        'xx_partner_email_layouts': fields.one2many('xx.partner.email.layout','partner_id','E-mail Layouts'),
        'xx_communication_type': fields.selection( [('post','Post'),('mail','E-mail')],'Communication Type'),        
    }

    _defaults = {
        'xx_communication_type': 'post',
    }