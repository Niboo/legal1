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

    purchase_csv_template = fields.Text(
        help=(
            'If defined, purchase orders sent by mail will get an additional '
            'attachment containing the order lines in CSV format. In this '
            'field you can specify the fields that should be present in the '
            'CSV lines. You can refer to the supplier information as '
            '"seller", the purchase line as "line" and the order itself as '
            '"order". If you only have one field, please add a trailing comma.'
        ))
