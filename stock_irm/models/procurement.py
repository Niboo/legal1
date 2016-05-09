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

    def run_scheduler(self, cr, uid, use_new_cursor=False, company_id=False, context=None):
        if context is None:
            context = {}

        ctx = context.copy()
        ctx['skip_reservation'] = True
        print "run sheduler mec"
        return super(ProcurementOrder, self).run_scheduler(cr, uid, use_new_cursor, company_id, context=ctx)


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_assign(self, cr, uid, ids, context=None):
        print context
        if context and context.get('skip_reservation', False) == True:
            print "retourne rien!"
            return {}
        else:
            print "fais le normalement"
            return super(StockMove, self).action_assign(cr, uid, ids, context)
