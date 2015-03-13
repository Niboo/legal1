from openerp.osv import orm, osv, fields

class xx_document_layout(osv.osv):
    
    _name = 'xx.document.layout'

    _columns = {
        'company_id': fields.many2one('res.company','Company'),
        'document_type': fields.selection([
            ('quotation', 'Quotation'),
            ('sale_order', 'Sale Order'),
            ('delivery_note', 'Delivery Note'),
            ('invoice', 'Invoice'),
            ], 
            'Document Type', required=True),
        'jasper_report': fields.many2one('ir.actions.report.xml','Layout',required=True,domain=[('jasper_report','=',True)]),
        'nb_of_copies': fields.float('# Copies', digits=(2,0)),
    }
    
    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
        'nb_of_copies': 1,
    }

class xx_email_layout(osv.osv):
    
    _name = 'xx.email.layout'

    _columns = {
        'company_id': fields.many2one('res.company','Company'),
        'document_type': fields.selection([
            ('quotation', 'Quotation'),
            ('sale_order', 'Sale Order'),
            ('delivery_note', 'Delivery Note'),
            ('invoice', 'Invoice'),
            ], 
            'Document Type', required=True),
        'email_template': fields.many2one('email.template','E-mail Template',required=True),
    }
    
    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }