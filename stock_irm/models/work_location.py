# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Jerome Guerriat
#    Copyright 2015 Niboo SPRL
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

from openerp import models, api, fields
from openerp.exceptions import ValidationError


class WorkLocation(models.Model):

    _inherit = "work_location"

    staging_location_id = fields.Many2one('stock.location', 'Staging Location ',
                                          required=True)

    @api.one
    @api.constrains('work_location_printer_ids')
    def check_single_label_printer(self):
        label_printer_type_id = self.env.ref('stock_irm.label_printer_type')
        printers = self.work_location_printer_ids
        label_printers = printers.filtered(
                lambda r: r.document_type_id.id == label_printer_type_id.id)
        
        if len(label_printers) > 1:
            raise ValidationError("""
You can only set a single label printer for each Work Location""")
