from openerp.osv import orm, osv, fields

class ir_attachment(osv.osv):
    
    _inherit = 'ir.attachment'

    _columns = {
        'xx_report_xml_id': fields.many2one('ir.actions.report.xml','Report XML'),
    }