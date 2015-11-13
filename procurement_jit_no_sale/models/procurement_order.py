# -*- coding: utf-8 -*-
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
            print "Not running"
            return True
        return super(ProcurementOrder, self).run(autocommit=autocommit)
