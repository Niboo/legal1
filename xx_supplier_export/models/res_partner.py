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

from openerp import api, models, fields, exceptions
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('purchase_csv_template')
    def onchange_purchase_csv_template(self):
        template = False
        try:
            template = safe_eval(self.purchase_csv_template or '[]', {
                'order': self.env['purchase.order'],
                'line': self.env['purchase.order.line'],
                'seller': self.env['product.supplierinfo'],
            })
        except Exception, e:
            raise exceptions.ValidationError(
                _('The CSV template does not have a valid format: %s') % e)
        if not isinstance(template, (list, tuple)):
            raise exceptions.ValidationError(
                _('The CSV template does not have a valid format. '
                  'It should consist of comma separated field references '
                  'or literals.'))

    @api.onchange('purchase_csv_header')
    def onchange_purchase_csv_header(self):
        header = False
        try:
            header = safe_eval(self.purchase_csv_header or '[]', {
                'order': self.env['purchase.order'],
            })
        except Exception, e:
            raise exceptions.ValidationError(
                _('The CSV header does not have a valid format: %s') % e)
        if not isinstance(header, (list, tuple)):
            raise exceptions.ValidationError(
                _('The CSV header does not have a valid format. '
                  'It should consist of comma separated literals enclosed '
                  'in quotes, or references to the "order" object.'))

    purchase_csv_template = fields.Text(
        help=(
            'If defined, purchase orders sent by mail will get an additional '
            'attachment containing the order lines in CSV format. In this '
            'field you can specify the fields that should be present in the '
            'CSV lines. You can refer to the supplier information as '
            '"seller", the purchase line as "line" and the order itself as '
            '"order". If you only have one field, please add a trailing '
            'comma.'),
        string='CSV Template',
    )
    purchase_csv_header = fields.Char(
        help=(
            'Optional header for the CSV export of purchase orders. This will '
            'usually consist of fixed values. Enter a comma separated string '
            'of such values, enclosed in quotes.'),
        string='CSV Header',
    )
    purchase_csv_quotechar = fields.Selection(
        [('"', '"'), ('\'', '\'')], string="CSV Quote Character",
        default='"', required=True)
    purchase_csv_delimiter = fields.Selection(
        [(',', ','), (';', ';')], string="CSV Field Separator",
        default=',', required=True)
    purchase_csv_quoting = fields.Selection(
        [('MINIMAL', 'Only for values containing the separator or the '
          'quote character'),
         ('NONNUMERIC', 'Quote all strings')],
        default='MINIMAL', required=True, string='Quoting')
