from openerp.osv import orm, osv, fields

class res_company(osv.osv):
    
    _inherit = 'res.company'

    _columns = {
        'xx_announcement': fields.text('Announcement', translate=True),
        'xx_document_layouts': fields.one2many('xx.document.layout','company_id','Print Layouts'),
        'xx_email_layouts': fields.one2many('xx.email.layout','company_id','E-mail Layouts'),
        'xx_report_name': fields.char('Report Name', size=240),
        'xx_report_header_image': fields.binary("Report Header Image"),
        'xx_report_footer_image': fields.binary("Report Footer Image"),
    }