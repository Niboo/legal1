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

from openerp import models, api


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    # upstream method needs a decorator to designate the template_id argument
    @api.model
    def generate_email_batch(self, template_id, res_ids, fields=None):
        """ Generate CSV files for purchase orders whose supplier have a CSV
        template configured and add to the email """
        res = super(EmailTemplate, self).generate_email_batch(
            template_id, res_ids, fields=fields)
        if template_id in ([
                self.env.ref('purchase.email_template_edi_purchase_done').id,
                self.env.ref('purchase.email_template_edi_purchase').id]):
            pass  # do something
        return res
