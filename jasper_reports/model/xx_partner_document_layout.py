from openerp.osv import orm, osv, fields

class xx_partner_document_layout(osv.osv):
    
    _name = 'xx.partner.document.layout'

    _columns = {
        'partner_id': fields.many2one('res.partner','Partner'),
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
        'nb_of_copies': 1,
    }

class xx_partner_email_layout(osv.osv):
    
    _name = 'xx.partner.email.layout'

    _columns = {
        'partner_id': fields.many2one('res.partner','Partner'),
        'document_type': fields.selection([
            ('quotation', 'Quotation'),
            ('sale_order', 'Sale Order'),
            ('delivery_note', 'Delivery Note'),
            ('invoice', 'Invoice'),
            ], 
            'Document Type', required=True),
        'email_template': fields.many2one('email.template','E-mail Template',required=True),
    }