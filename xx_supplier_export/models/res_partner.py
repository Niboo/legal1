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

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_csv_template = fields.Text(
        help=(
            'If defined, purchase orders sent by mail will get an additional '
            'attachment containing the order lines in CSV format. In this '
            'field you can specify the fields that should be present in the '
            'CSV lines. You can refer to the supplier information as '
            '"seller", the purchase line as "line" and the order itself as '
            '"order". Keep the enclosing square brackets to make the value '
            'of this field a valid Python list.'))
