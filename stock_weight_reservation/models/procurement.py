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


class ProcurementOrder(models.Model):

    _inherit = "procurement.order"

    @api.model
    def run_scheduler(self, use_new_cursor=False, company_id=False):
        return super(ProcurementOrder, self.with_context(skip_reservation=True)).run_scheduler(use_new_cursor, company_id)


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def action_assign(self):
        # do not assign procurement that are run through the scheduler
        if self._context and self._context.get('skip_reservation', False) == True:
            # skip reservation
            return {}
        else:
            return super(StockMove, self).action_assign()
