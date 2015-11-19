# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 DynApps <http://www.dynapps.be>
#
#    @author: Stefan Rijnhart <stefan.rijnhart@dynapps.nl>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import csv
import cStringIO
import codecs
from base64 import b64encode
from openerp import models, api
from openerp.tools.safe_eval import safe_eval


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def get_csv_export(self):
        """ Generate the CSV export for the current order based on the
        csv template field on the supplier.

        @returns tuple (filename, base64 encoded file)
        """
        self.ensure_one()
        csv_template = self.partner_id.purchase_csv_template
        if not csv_template or not self.order_line:
            return False

        def clean(data):
            """ Replace any falsy values with the empty string """
            col = 0
            for field in data:
                if not data[col]:
                    data[col] = ''
                col += 1
            return data

        with cStringIO.StringIO() as output:
            writer = UnicodeWriter(output)
            for line in self.order_line:
                data = safe_eval(csv_template, {
                    'order': self,
                    'line': line,
                    'seller': self.env['product.supplierinfo'].search(
                        [('name', '=', self.partner_id.id),
                         ('product_tmpl_id', '=',
                          line.product_id.product_tmpl_id.id)],
                        limit=1)
                })
                writer.writerow(clean(data))
            csv_export = output.getvalue()
        return "%s.csv" % self.name, b64encode(csv_export)
