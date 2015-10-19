# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import fields, models
from openerp.tools.translate import _
from collections import defaultdict
from openerp import SUPERUSER_ID


class stock_picking_wave(models.Model):
    _inherit = 'stock.picking.wave'

    # Easiest is to just extend this model for reporting
    wave_location_ids = fields.One2many('wave_location', 'wave_id', 'Wave Picking Locations', readonly=True)

    def print_wave(self, cr, uid, ids, context=None):
        context = dict(context or {})

        loc_list = set()
        q_dict = defaultdict(list)
        for wave in self.browse(cr, uid, ids, context=context):
            for picking in wave.picking_ids:
                package_id = False
                if not picking.packages_assigned:
                    package_vals = {
                        'name': picking.move_lines[0].group_id.name,
                    }
                    package_id = self.pool.get('stock.quant.package').create(cr, uid, package_vals, context=context)
                    self.pool.get('stock.picking').write(cr, uid, picking.id, {'packages_assigned': True}, context=context)
                for move_line in picking.move_lines:
                    for quant in move_line.reserved_quant_ids:
                        if package_id and not quant.package_id:
                            self.pool.get('stock.quant').write(cr, SUPERUSER_ID, quant.id, {'package_id': package_id}, context=context)
                        elif quant.package_id:
                            package_id = quant.package_id.id
                        # We can't use write(); this field is a readonly function field with a store parameter.
                        # Changing that would be more invasive than just doing a cursor write here.
                        cr.execute("UPDATE stock_quant_package SET location_id=%s WHERE id=%s" % (quant.location_id.id, package_id))
                        loc_list.add(quant.location_id)
                        q_dict[quant.location_id.id].append(quant)
            if not loc_list:
                raise osv.except_osv(_('Error!'), _('Nothing to print.'))
            loc_list = sorted(list(loc_list), lambda x, y: cmp(x.display_name, y.display_name))
            wvals = []
            to_delete_wave_locs = [x.id for x in wave.wave_location_ids]
            self.pool.get('wave_location').unlink(cr, uid, to_delete_wave_locs, context=context)
            # For determining box number later on; wave.picking_ids is not a list, so index won't work on it.
            picking_ids = [x.id for x in wave.picking_ids]
            parent_location_id = 0
            for loc in loc_list:
                # TODO: get rid of this, work with temp vars in the qweb template
                for quant in q_dict[loc.id]:
                    if loc.location_id.id != parent_location_id:
                        parent_location_id = loc.location_id.id
                        new_parent_location = True
                    else:
                        new_parent_location = False
                    vdict = {
                        'wave_id': wave.id,
                        'location_id': loc.id,
                        'product_id': quant.product_id.id,
                        'qty': quant.qty,
                        'picking_id': quant.reservation_id.picking_id.id,
                        'new_parent_location': new_parent_location,
                    }
                    wvals.append((0, 0, vdict))
                    # Put box nbr on picking
                    self.pool.get('stock.picking').write(cr, uid, quant.reservation_id.picking_id.id,
                        {'box_nbr': picking_ids.index(quant.reservation_id.picking_id.id) + 1,},
                        context=context)
            self.write(cr, uid, wave.id, {'wave_location_ids': wvals}, context=context)
        context['active_ids'] = ids
        context['active_model'] = 'stock.picking.wave'
        rep = self.pool.get("report")
        return rep.get_action(cr, uid, [], 'report.picking_wave', context=context)

    def get_user_name_picking(self):
        uname_arr = self.user_id.name.split()[:2]
        if len(uname_arr) > 1:
            uname_arr[1] = uname_arr[1][0]
            retval =  ' '.join(uname_arr).title()
        else:
            retval =  self.user_id.name
        return '%s.' % (retval, )

    def print_picking(self, cr, uid, ids, context=None):
        '''
        This function print the report for all picking_ids associated to the picking wave
        '''
        context = dict(context or {})
        picking_ids = []
        for wave in self.browse(cr, uid, ids, context=context):
            picking_ids += [picking.id for picking in wave.picking_ids]
        if not picking_ids:
            raise osv.except_osv(_('Error!'), _('Nothing to print.'))
        context['active_ids'] = picking_ids
        context['active_model'] = 'stock.picking'
        return self.pool.get("report").get_action(cr, uid, [], 'xx_report_delivery_extended.report_delivery_master', context=context)

class wave_location(models.Model):
    _name = 'wave_location'
    _description = 'Wave Picking Location'

    wave_id = fields.Many2one('stock.picking.wave', 'Picking Wave', required=True)
    location_id = fields.Many2one('stock.location', 'Source Location', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    qty = fields.Integer('Quantity', required=True)
    box_nbr = fields.Integer('Box #', related="picking_id.box_nbr")
    picking_id = fields.Many2one('stock.picking', 'Picking', required=True)
    new_parent_location = fields.Boolean('New Parent Location')
