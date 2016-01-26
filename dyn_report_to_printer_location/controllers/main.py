from openerp.addons.report.controllers.main import ReportController
from openerp.http import route


class NoAuthBarcode(ReportController):

    @route(auth="none")
    def report_barcode(
            self, type, value, width=600, height=100, humanreadable=0):
        """ Disable auth on the barcode generator API, so that we can call
        it from the cheap threads that we create for printing asynchronously
        (To be reconsidered as we reimplemented asynchronous printing using the
        connector framework.)
        """
        return super(NoAuthBarcode, self).report_barcode(
            type, value, width=width, height=height,
            humanreadable=humanreadable)
