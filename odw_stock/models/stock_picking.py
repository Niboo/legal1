# coding: utf-8
from openerp import models


class Picking(models.Model):
    _inherit = 'stock.picking'

    def _register_hook(self, cr):
        """ Force retrieving values for the related field
        location_dest_id without prefetching by setting a context value.
        Monkeypatch this onto the model's field instance. """
        field = self._columns['location_dest_id']
        if not hasattr(field, '_odw_stock_related_read'):

            field._odw_stock_related_read = field._fnct

            def _related_read(
                    self, obj, cr, uid, ids, field_name, args, context=None):
                context = dict(context or {})
                context.update(prefetch_fields=False)
                return self._odw_stock_related_read(
                    obj, cr, uid, ids, field_name, args, context=context)

            field._fnct = lambda *args, **kwargs: _related_read(
                field, *args, **kwargs)

        return super(Picking, self)._register_hook(cr)
