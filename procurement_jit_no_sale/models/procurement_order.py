# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 DynApps <http://www.dynapps.be>
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
from openerp.addons.procurement_jit.procurement_jit import procurement_order


@api.cr_uid
@api.returns('self', lambda value: value.id)
def create(self, cr, uid, vals, context=None):
    context = context or {}
    procurement_id = super(procurement_order, self).create(
        cr, uid, vals, context=context)
    if not vals.get('sale_line_id') and not context.get(
            'procurement_autorun_defer'):
        self.run(cr, uid, [procurement_id], context=context)
        self.check(cr, uid, [procurement_id], context=context)
    return procurement_id


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def __init__(self, pool, cr):
        """ Monkeypatch our version of create() into the original model class..
        This would normally happen in _register_hook, but as it turns out,
        tests run before _register_hook is called """
        res = super(ProcurementOrder, self).__init__(pool, cr)
        procurement_order.create = create
        return res

    @api.multi
    def run(self, autocommit=False):
        """ Prevent the procurements to run after a sale order's move lines
        are created """
        if self.env.context.get('procurement_do_not_run'):
            return True
        return super(ProcurementOrder, self).run(autocommit=autocommit)
