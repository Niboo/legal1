from openerp import models
from openerp.addons.procurement_jit.procurement_jit import procurement_order


def create(self, cr, uid, vals, context=None):
    context = context or {}
    procurement_id = super(procurement_order, self).create(
        cr, uid, vals, context=context)
    if not context.get('procurement_autorun_defer'):
        self.run(cr, uid, [procurement_id], context=context)
        self.check(cr, uid, [procurement_id], context=context)
    return procurement_id


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _register_hook(self, cr):
        res = super(ProcurementOrder, self)._register_hook(cr)
        procurement_order.create = create
        return res
