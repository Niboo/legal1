# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 DynApps <http://www.dynapps.be>
#
#    @author Stefan Rijnhart <stefan.rijnhart@dynapps.be>
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
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_dropshipping = fields.Boolean(
        compute="_get_is_dropshipping")

    @api.multi
    def _get_is_dropshipping(self):
        """ If any line has any other route or any procurement set to
        anything other than dropshipping, this is not a dropshipping order.
        """
        route = self.env.ref('stock_dropshipping.route_drop_shipping')
        route_set = set([route])
        for order in self:
            order.is_dropshipping = True
            for line in self.order_line:
                procurements = line.procurement_ids.filtered(
                    lambda proc: proc.state != 'cancel')
                for proc in procurements:
                    if set(proc.route_ids) != route_set:
                        order.is_dropshipping = False
                        break
                if not procurements and (
                        not line.route_id or line.route_id != route):
                    order.is_dropshipping = False
                    break

    @api.multi
    def rollback_dropshipping(self):
        """ Reset any procurements from dropshipping to default route """
        self.ensure_one()
        if not self.is_dropshipping:
            raise UserError(_('This is not a dropshipping order.'))
        procurements = self.order_line.mapped('procurement_ids').filtered(
            lambda proc: proc.state not in ('cancel', 'draft'))
        draft_proc = self.order_line.mapped('procurement_ids').filtered(
            lambda proc: proc.state == 'draft')
        if any([proc.state == 'done' for proc in procurements]):
            raise UserError(
                _('At least one procurement has already been '
                  'fully processed. Cannot rollback dropshipping.'))
        procurements.cancel()
        if not all([proc.state == 'cancel' for proc in procurements]):
            raise UserError(
                _('Not all procurements from this sale order could be reset. '
                  'Please check the procurements manually.'))
        procurements.write({'route_ids': [(6, 0, [])]})
        procurements.reset_to_confirmed()
        draft_proc.write({'route_ids': [(6, 0, [])]})
        self.order_line.write({'route_id': False})
