##############################################################################
#
# Copyright (c) 2008-2012 NaN Projectes de Programari Lliure, S.L.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import os
import openerp.report
from openerp import pooler
from openerp.osv import orm, osv, fields
from openerp import tools
import tempfile
#import netsvc
import logging
import time
from datetime import datetime

from JasperReports import *

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from pyPdf import PdfFileWriter, PdfFileReader
except ImportError:
    raise osv.except_osv(
        "jasper_reports needs pyPdf",
        """To install the module "jasper_reports" please ask your administrator to install the pyPdf package."""
    )


_logger = logging.getLogger(__name__)

# Determines the port where the JasperServer process should listen with its XML-RPC server for incomming calls
tools.config['jasperport'] = tools.config.get('jasperport', 8090)

# Determines the file name where the process ID of the JasperServer process should be stored
tools.config['jasperpid'] = tools.config.get('jasperpid', 'openerp-jasper.pid')

# Determines if temporary files will be removed
tools.config['jasperunlink'] = tools.config.get('jasperunlink', True)

class _format(object):
    def set_value(self, cr, uid, name, object, field, lang_obj):
        self.object = object
        self._field = field
        self.name = name
        self.lang_obj = lang_obj

class _float_format(float, _format):
    def __init__(self,value):
        super(_float_format, self).__init__()
        self.val = value or 0.0

    def __str__(self):
        digits = 2
        if hasattr(self,'_field') and getattr(self._field, 'digits', None):
            digits = self._field.digits[1]
        if hasattr(self, 'lang_obj'):
            return self.lang_obj.format('%.' + str(digits) + 'f', self.name, True)
        return str(self.val)

class _date_format(str, _format):
    def __init__(self,value):
        super(_date_format, self).__init__()
        self.val = value and str(value) or ''

    def __str__(self):
        if self.val:
            if getattr(self,'name', None):
                date = datetime.strptime(self.name[:get_date_length()], DEFAULT_SERVER_DATE_FORMAT)
                return date.strftime(str(self.lang_obj.date_format))
        return self.val

class _dttime_format(str, _format):
    def __init__(self,value):
        super(_dttime_format, self).__init__()
        self.val = value and str(value) or ''

    def __str__(self):
        if self.val and getattr(self,'name', None):
            return datetime.strptime(self.name, DEFAULT_SERVER_DATETIME_FORMAT)\
                   .strftime("%s %s"%(str(self.lang_obj.date_format),
                                      str(self.lang_obj.time_format)))
        return self.val

class _int_format(int, _format):
    def __init__(self,value):
        super(_int_format, self).__init__()
        self.val = value or 0

    def __str__(self):
        if hasattr(self,'lang_obj'):
            return self.lang_obj.format('%.d', self.name, True)
        return str(self.val)

_fields_process = {
    'float': _float_format,
    'date': _date_format,
    'integer': _int_format,
    'datetime' : _dttime_format
}

class browse_record_list(list):
    def __init__(self, lst, context):
        super(browse_record_list, self).__init__(lst)
        self.context = context

    def __getattr__(self, name):
        res = browse_record_list([getattr(x,name) for x in self], self.context)
        return res

    def __str__(self):
        return "browse_record_list("+str(len(self))+")"

class Report:
    def __init__(self, name, cr, uid, ids, data, context):
        self.name = name
        self.cr = cr
        self.uid = uid
        self.data = data
        if ids:
            self.ids = ids
            self.model = self.data.get('model', False) or context.get('active_model', False)
        else:
            self.ids = context.get('active_ids')
            self.model = context.get('active_model', False)
        self.context = context or {}
        self.pool = pooler.get_pool( self.cr.dbname )
        self.reportPath = None
        self.report = None
        self.temporaryFiles = []
        self.outputFormat = 'pdf'
        self.time = time

    def execute(self):
        """
        If self.context contains "return_pages = True" it will return the number of pages
        of the generated report.
        """
        logger = logging.getLogger(__name__)

        # * Get report path *
        # Not only do we search the report by name but also ensure that 'report_rml' field
        # has the '.jrxml' postfix. This is needed because adding reports using the <report/>
        # tag, doesn't remove the old report record if the id already existed (ie. we're trying
        # to override the 'purchase.order' report in a new module). As the previous record is
        # not removed, we end up with two records named 'purchase.order' so we need to destinguish
        # between the two by searching '.jrxml' in report_rml.
        aname=None
        report_xml_ids = self.pool.get('ir.actions.report.xml').search(self.cr, self.uid, [('report_name', '=', self.name[7:]),('report_rml','ilike','.jrxml')], context=self.context)
        report_xml = self.pool.get('ir.actions.report.xml').browse(self.cr, self.uid, report_xml_ids[0])
        self.context.update({'report_xml_id':report_xml.id})
        
        model_obj = self.pool.get(self.model).browse(self.cr, self.uid, self.ids[0], context=self.context) #list_class=browse_record_list, fields_process=_fields_process deprecated in 8.0 rc1
        attach = report_xml.attachment
        if attach:
            aname = eval(attach, {'object':model_obj, 'time':self.time})
            if report_xml.attachment_use and self.context.get('attachment_use', True):
                attach_ids = self.pool.get('ir.attachment').search(self.cr, self.uid, [('datas_fname','=',aname),('res_model','=',self.model),('res_id','=',model_obj.id),('xx_report_xml_id','=',report_xml.id)])
                if attach_ids:
                    brow_rec = self.pool.get('ir.attachment').browse(self.cr, self.uid, attach_ids[0])
                    if brow_rec.datas:
                        data = base64.decodestring(brow_rec.datas)
                        return ( data, self.outputFormat )

        if report_xml.jasper_output:
            self.outputFormat = report_xml.jasper_output
        self.reportPath = report_xml.report_rml
        self.reportPath = os.path.join( self.addonsPath(), self.reportPath )
        if not os.path.lexists(self.reportPath):
            self.reportPath = self.addonsPath(path=report_xml.report_rml)

        # Get report information from the jrxml file
        logger.info("Requested report: '%s'" % self.reportPath)
        self.report = JasperReport( self.reportPath )

        # Create temporary input (XML) and output (PDF) files 
        fd, dataFile = tempfile.mkstemp()
        os.close(fd)
        fd, outputFile = tempfile.mkstemp()
        os.close(fd)
        self.temporaryFiles.append( dataFile )
        self.temporaryFiles.append( outputFile )
        logger.info("Temporary data file: '%s'" % dataFile)

        import time
        start = time.time()

        # If the language used is xpath create the xmlFile in dataFile.
        if self.report.language() == 'xpath':
            if self.data.get('data_source','model') == 'records':
                generator = CsvRecordDataGenerator(self.report, self.data['records'] )
            else:
                generator = CsvBrowseDataGenerator( self.report, self.model, self.pool, self.cr, self.uid, self.ids, self.context )
            generator.generate( dataFile )
            self.temporaryFiles += generator.temporaryFiles
        
        subreportDataFiles = []
        for subreportInfo in self.report.subreports():
            subreport = subreportInfo['report']
            if subreport.language() == 'xpath':
                message = 'Creating CSV '
                if subreportInfo['pathPrefix']:
                    message += 'with prefix %s ' % subreportInfo['pathPrefix']
                else:
                    message += 'without prefix '
                message += 'for file %s' % subreportInfo['filename']
                logger.info("%s" % message)

                fd, subreportDataFile = tempfile.mkstemp()
                os.close(fd)
                subreportDataFiles.append({
                    'parameter': subreportInfo['parameter'],
                    'dataFile': subreportDataFile,
                    'jrxmlFile': subreportInfo['filename'],
                })
                self.temporaryFiles.append( subreportDataFile )

                if subreport.isHeader():
                    generator = CsvBrowseDataGenerator( subreport, 'res.users', self.pool, self.cr, self.uid, [self.uid], self.context )
                elif self.data.get('data_source','model') == 'records':
                    generator = CsvRecordDataGenerator( subreport, self.data['records'] )
                else:
                    generator = CsvBrowseDataGenerator( subreport, self.model, self.pool, self.cr, self.uid, self.ids, self.context )
                generator.generate( subreportDataFile )
                

        # Call the external java application that will generate the PDF file in outputFile
        pages = self.executeReport( dataFile, outputFile, subreportDataFiles )
        elapsed = (time.time() - start) / 60
        logger.info("ELAPSED: %f" % elapsed)

        # Read data from the generated file and return it
        f = open( outputFile, 'rb')
        try:
            data = f.read()
        finally:
            f.close()

        # Remove all temporary files created during the report
        if tools.config['jasperunlink']:
            for file in self.temporaryFiles:
                try:
                    os.unlink( file )
                except os.error, e:
                    logger.warning("Could not remove file '%s'." % file )
        self.temporaryFiles = []

        # Terms & Conditions functionality
        if report_xml.report_type == 'pdf':    
            # Check conditions to add or not
            rule_obj = self.pool.get('term.rule')
            if rule_obj:        
                if hasattr(report_xml, 'report_name'):
                    rule_ids = rule_obj.search(self.cr, self.uid, [('report_name','=',report_xml.report_name),])
                    if len(rule_ids):
                        valid_rules = []
                        for rule in rule_obj.browse(self.cr, self.uid, rule_ids, context=self.context):
                            logger.debug("Checking rule %s for report %s, with data: %s", rule.term_id.name, report_xml.report_name, data)
                    
                            if rule.company_id and hasattr(model_obj, 'company_id'):
                                if rule.company_id.id != model_obj.company_id.id:
                                    logger.debug("Company id's did not match !")
                                    continue
                                else:
                                    logger.debug("Company id's matched !")
                    
                            if rule.condition:
                                env = {
                                    'object': model_obj,
                                    'report': report_xml,
                                    'data': data,
                                    'date': time.strftime('%Y-%m-%d'),
                                    'time': time,
                                    'context': context,
                                }
                                # User has specified a condition, check it and return res when not met
                                if not safe_eval(rule.condition, env):
                                    logger.debug("Term condition not met !")
                                    continue
                                else:
                                    logger.debug("Term condition met !")
                    
                            valid_rules += [ rule ]
                    
                        output = PdfFileWriter()
                        reader = PdfFileReader( StringIO(data) )
                    
                        for rule in valid_rules:
                            if rule.term_id.mode == 'begin':
                                att = PdfFileReader( StringIO(base64.decodestring(rule.term_id.pdf)) )
                                map(output.addPage, att.pages)
                    
                        for page in reader.pages:
                            output.addPage( page )
                            for rule in valid_rules:
                                if rule.term_id.mode == 'duplex':
                                    att = PdfFileReader( StringIO(base64.decodestring(rule.term_id.pdf)) )
                                    map(output.addPage, att.pages)
                    
                        for rule in valid_rules:
                            if rule.term_id.mode == 'end':
                                att = PdfFileReader( StringIO(base64.decodestring(rule.term_id.pdf)) )
                                map(output.addPage, att.pages)
                    
                        buf = StringIO()
                        output.write(buf)
                        data = buf.getvalue()        
        
        # Attachment functionality
        if aname:
            # Remove the default_type entry from the context: this
            # is for instance used on the account.account_invoices
            # and is thus not intended for the ir.attachment type
            # field.
            ctx = dict(self.context)
            ctx.pop('default_type', None)
            self.pool.get('ir.attachment').create(self.cr, self.uid, {
                'name': aname,
                'datas': base64.encodestring(data),
                'datas_fname': aname,
                'res_model': self.model,
                'res_id': model_obj.id,
                'xx_report_xml_id': report_xml.id,
                }, context=ctx
            )

        if self.context.get('return_pages'):
            return ( data, self.outputFormat, pages )
        else:
            return ( data, self.outputFormat )

    def path(self):
        return os.path.abspath(os.path.dirname(__file__))

    def addonsPath(self, path=False):
        if path:
            report_module = path.split(os.path.sep)[0]
            for addons_path in tools.config['addons_path'].split(','):
                if os.path.lexists(addons_path+os.path.sep+report_module):
                    return os.path.normpath( addons_path+os.path.sep+path )

        return os.path.dirname( self.path() )

    def systemUserName(self):
        if os.name == 'nt':
            import win32api
            return win32api.GetUserName()
        else:
            import pwd
            return pwd.getpwuid(os.getuid())[0]

    def dsn(self):
        host = tools.config['db_host'] or 'localhost'
        port = tools.config['db_port'] or '5432'
        dbname = self.cr.dbname
        return 'jdbc:postgresql://%s:%s/%s' % ( host, port, dbname )
    
    def userName(self):
        return tools.config['db_user'] or self.systemUserName()

    def password(self):
        return tools.config['db_password'] or ''

    def executeReport(self, dataFile, outputFile, subreportDataFiles):
        locale = self.context.get('lang', 'en_US')
        
        connectionParameters = {
            'output': self.outputFormat,
            #'xml': dataFile,
            'csv': dataFile,
            'dsn': self.dsn(),
            'user': self.userName(),
            'password': self.password(),
            'subreports': subreportDataFiles,
        }
        parameters = {
            'STANDARD_DIR': self.report.standardDirectory(),
            'REPORT_LOCALE': locale,
            'IDS': self.ids,
        }
        if 'parameters' in self.data:
            parameters.update( self.data['parameters'] )

        server = JasperServer( int( tools.config['jasperport'] ) )
        server.setPidFile( tools.config['jasperpid'] )
        return server.execute( connectionParameters, self.reportPath, outputFile, parameters )


def register_jasper_report(report_name, model_name):
    name = 'report.%s' % report_name
    return report_jasper( name, model_name )

class report_jasper(openerp.report.interface.report_int):
    def __init__(self, name, model, parser=None ):
        super(report_jasper, self).__init__(name,False)
        self.model = model
        self.parser = parser

    def create(self, cr, uid, ids, data, context):
        name = self.name
        if self.parser:
            d = self.parser( cr, uid, ids, data, context )
            ids = d.get( 'ids', ids )
            name = d.get( 'name', self.name )
            # Use model defined in report_jasper definition. Necesary for menu entries.
            data['model'] = d.get( 'model', self.model )
            data['records'] = d.get( 'records', [] )
            # data_source can be 'model' or 'records' and lets parser to return
            # an empty 'records' parameter while still executing using 'records'
            data['data_source'] = d.get( 'data_source', 'model' )
            data['parameters'] = d.get( 'parameters', {} )
        report = Report( name, cr, uid, ids, data, context )
        #return ( report.execute(), 'pdf' )
        return report.execute()

class ir_actions_report_xml(osv.osv):
    _inherit = 'ir.actions.report.xml'
    
    def _lookup_report(self, cr, name):
        """
        Look up a report definition.
        """
        import operator
        import os
        opj = os.path.join
        new_report = None

        if 'report.' + name in openerp.report.interface.report_int._reports:
            new_report = openerp.report.interface.report_int._reports['report.' + name]
            if not isinstance(new_report, report_jasper):
                new_report = None
        else:
            cr.execute("SELECT * FROM ir_act_report_xml WHERE report_name=%s and jasper_report='t'", (name,))
            record = cr.dictfetchone()
            if record:
                if record['parser']:
                    parser = operator.attrgetter(record['parser'])(openerp.addons)
                    kwargs = { 'parser': parser }
                else:
                    kwargs = {}

                new_report = register_jasper_report(record['report_name'], record['model'])
            else:
                new_report = None

        if new_report:
            return new_report
        else:
            return super(ir_actions_report_xml, self)._lookup_report(cr, name)

ir_actions_report_xml()

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
