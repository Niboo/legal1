# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import fields, models
from openerp.tools.translate import _
from collections import defaultdict
from openerp import SUPERUSER_ID


class stock_picking_wave(models.Model):
    _inherit = 'stock.picking.wave'

    # Easiest is to just extend this model for reporting
    wave_location_ids = fields.One2many(
        'wave_location', 'wave_id', 'Wave Picking Locations', readonly=True)

    def print_wave(self, cr, uid, ids, context=None):
        context = dict(context or {})

        loc_list = set()
        q_dict = defaultdict(list)
        for wave in self.browse(cr, uid, ids, context=context):
            if not wave.user_id:
                raise osv.except_osv(_('Error!'), 'There is no responsible for this wave. Please assign one before printing.')
            # Oops, new API
            # temp_location = self.env.ref(
            #     'putaway_apply.default_temp_location'):
            index = 0
            for picking in wave.picking_ids:
                package_id = False
                if not picking.packages_assigned:
                    package_vals = {
                        'name': picking.move_lines[0].group_id.name,
                    }
                    package_id = self.pool.get('stock.quant.package').create(cr, uid, package_vals, context=context)
                    self.pool.get('stock.picking').write(cr, uid, picking.id, {'packages_assigned': True}, context=context)
                for move_line in picking.move_lines:
                    if not move_line.reserved_quant_ids:
                        self.pool.get('stock.move').do_unreserve(cr, uid, move_line.id, context=context)
                        self.pool.get('stock.picking').action_assign(cr, uid, [picking.id], context=context)
                        move_line = self.pool.get('stock.move').browse(cr, uid, move_line.id, context=context)
                        if not move_line.reserved_quant_ids:
                            raise osv.except_osv(_('Error!'), 'There is no reservable stock for product %s, in picking %s - you can remove it from the wave then try again.' % (move_line.product_id.name, picking.name))
                    for quant in move_line.reserved_quant_ids:
                        if package_id and not quant.package_id:
                            self.pool.get('stock.quant').write(cr, SUPERUSER_ID, quant.id, {'package_id': package_id}, context=context)
                        elif quant.package_id:
                            package_id = quant.package_id.id
                        else:
                            raise osv.except_osv(_('Error!'), 'There is no package for quant %s, in picking %s' % (move_line.name, picking.name))
                        # We can't use write(); this field is a readonly function field with a store parameter.
                        # Changing that would be more invasive than just doing a cursor write here.
                        if not quant.location_id:
                            raise osv.except_osv(_('Error!'), 'No location assigned to quant %s for move line %s, in picking %s' % (quant.name, move_line.name, picking.name))
                        cr.execute("UPDATE stock_quant_package SET location_id=%s WHERE id=%s" % (quant.location_id.id, package_id))
                        loc_list.add(quant.location_id)
                        q_dict[quant.location_id.id].append(quant)
                index += 1
                picking.write({'box_nbr': index})
            if not loc_list:
                raise osv.except_osv(_('Error!'), _('There are no locations for any quants assigned to the pickings. Please rectify this.'))
            loc_list = sorted(list(loc_list), lambda x, y: cmp(x.display_name, y.display_name))
            wvals = []
            to_delete_wave_locs = [x.id for x in wave.wave_location_ids]
            self.pool.get('wave_location').unlink(cr, uid, to_delete_wave_locs, context=context)
            parent_location_id = 0
            wave.refresh()  # Reload box nbr, hopefully
            for loc in loc_list:
                # TODO: get rid of this, work with temp vars in the qweb template
                for quant in q_dict[loc.id]:
                    # Put box nbr on picking
                    quant.reservation_id.picking_id.write({'box_nbr': box_nbr,})
                    if loc.location_id.id != parent_location_id:
                        parent_location_id = loc.location_id.id
                        new_parent_location = True
                    else:
                        new_parent_location = False
                    vdict = {
                        'location_id': loc.id,
                        'product_id': quant.product_id.id,
                        'qty': quant.qty,
                        'picking_id': quant.reservation_id.picking_id.id,
                        'new_parent_location': new_parent_location,
                        'box_nbr': str(quant.reservation_id.picking_id.box_nbr or 0),
                    }
                    wvals.append((0, 0, vdict))
            self.write(cr, uid, wave.id, {'wave_location_ids': wvals}, context=context)
        context['active_ids'] = ids
        context['active_model'] = 'stock.picking.wave'
        rep = self.pool.get("report")
        return rep.get_action(cr, uid, [], 'report.picking_wave', context=context)

    def get_user_name_picking(self):
        if not self.user_id:
            return 'N/A'
        uname_arr = self.user_id.name.split()[:2]
        if len(uname_arr) > 1:
            uname_arr[1] = uname_arr[1][0]
            retval =  ' '.join(uname_arr).title()
        else:
            retval =  self.user_id.name
        return '%s' % (retval, )

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
    box_nbr = fields.Char(
        'Box #',
        help='Box number in this wave, or POG if applicable')
    picking_id = fields.Many2one('stock.picking', 'Picking', required=True)
    new_parent_location = fields.Boolean('New Parent Location')
