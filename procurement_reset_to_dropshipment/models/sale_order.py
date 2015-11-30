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

from openerp import models, api
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def reset_to_dropshipment(self):
        """ Reset the route on an unconfirmed and unprocessed order to
        dropshipping """
        self.ensure_one()
        if self.state not in ('draft', 'sent', 'manual', 'progress'):
            raise UserError(
                _('Cannot reset the route of an order in state %s') % (
                    self.state))
        route = self.env.ref('stock_dropshipping.route_drop_shipping')
        procurements = self.env['procurement.order']
        for line in self.with_context(active_test=False).order_line:
            if not line.procurement_ids:
                continue
            for proc in line.procurement_ids:
                if proc.state in ('done', 'running', 'exception'):
                    raise UserError(
                        _('Cannot reset an order with a procurement in '
                          'state %s') % (proc.state))
            procurements += line.procurement_ids.filtered(
                lambda proc: proc.state in ('draft', 'confirmed'))
        self.order_line.write({'route_id': route.id})
        if procurements:
            return procurements.write({'route_ids': [(6, 0, [route.id])]})

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        """ Set procurement orders to inactive when coming from sales orders.
        The scheduler will set all orders older than a small timeframe to
        active """
        res = super(SaleOrder, self)._prepare_order_line_procurement(
            order, line, group_id=group_id)
        res['active'] = False
        return res
