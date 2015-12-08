# -*- coding: utf-8 -*-
import re
from openerp.osv import osv
from openerp.exceptions import Warning as UserError
from openerp import fields, models, api
from openerp.tools.translate import _
from collections import defaultdict


class stock_picking_wave(models.Model):
    _inherit = 'stock.picking.wave'

    # Easiest is to just extend this model for reporting
    wave_location_ids = fields.One2many(
        'wave_location', 'wave_id', 'Wave Picking Locations', readonly=True)

    @api.multi
    def print_wave(self):
        locations = self.env['stock.location']
        q_dict = defaultdict(list)  # mapping from location ids to quants
        for wave in self:
            if not wave.user_id:
                raise UserError(_(
                    'There is no responsible for this wave. '
                    'Please assign one before printing.'))
            index = 0
            temp_loc = self.env.ref('putaway_apply.default_temp_location')
            for picking in wave.picking_ids:
                package_id = False
                if not picking.packages_assigned:
                    package_vals = {
                        'name': picking.move_lines[0].group_id.name,
                    }
                    package_id = self.env['stock.quant.package'].create(
                        package_vals).id
                    picking.write({'packages_assigned': True})
                for move_line in picking.move_lines:
                    if not move_line.reserved_quant_ids:
                        move_line.do_unreserve()
                        picking.action_assign()
                        if not move_line.reserved_quant_ids:
                            raise UserError(_(
                                'There is no reservable stock for product %s, '
                                'in picking %s - you can remove it from the '
                                'wave then try again.') % (
                                move_line.product_id.name, picking.name))
                    for quant in move_line.reserved_quant_ids:
                        if package_id and not quant.package_id:
                            quant.sudo().write({'package_id': package_id})
                        elif quant.package_id:
                            package_id = quant.package_id.id
                        else:
                            raise UserError(
                                'There is no package for quant %s, in picking '
                                '%s' % (move_line.name, picking.name))
                        # We can't use write(); this field is a readonly
                        # function field with a store parameter. Changing that
                        # would be more invasive than just doing a cursor write
                        # here.
                        if not quant.location_id:
                            raise UserError(_(
                                'No location assigned to quant %s for move '
                                'line %s, in picking %s') % (
                                quant.name, move_line.name, picking.name))
                        self.env.cr.execute(
                            'UPDATE stock_quant_package SET location_id=%s '
                            'WHERE id=%s', (quant.location_id.id, package_id))
                        locations += quant.location_id
                        q_dict[quant.location_id.id].append(quant)
                index += 1
                picking.write({'box_nbr': index})
            if not locations:
                raise UserError(
                    _('There are no locations for any quants assigned to the '
                      'pickings. Please rectify this.'))
            wvals = []
            wave.wave_location_ids.unlink()
            parent_location_id = 0
            for loc in sorted(locations, key=lambda x: x.display_name):
                # TODO: get rid of this, work with temp vars in the qweb
                # template
                for quant in q_dict[loc.id]:
                    # Put box nbr on picking
                    if loc.location_id.id != parent_location_id:
                        parent_location_id = loc.location_id.id
                        new_parent_location = True
                    else:
                        new_parent_location = False
                    picking = quant.reservation_id.picking_id
                    if loc == temp_loc:  # display POG, not box number
                        # Strip off SO + year prefix to save space on the label
                        if re.match('(SO[0-9]{2})', picking.group_id.name):
                            destination = picking.group_id.name[4:]
                        else:
                            destination = picking.group_id.name
                        if picking.destination != destination:
                            picking.write({'destination': destination})
                    if not picking.destination:
                        picking.write({'destination': picking.name})
                    vdict = {
                        'location_id': loc.id,
                        'product_id': quant.product_id.id,
                        'qty': quant.qty,
                        'picking_id': picking.id,
                        'new_parent_location': new_parent_location,
                    }
                    wvals.append((0, 0, vdict))
            wave.write({'wave_location_ids': wvals})
        return self.env['report'].with_context(
            active_ids=self.ids, active_model=self._name).get_action(
            self, 'report.picking_wave')

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
    picking_id = fields.Many2one('stock.picking', 'Picking', required=True)
    destination = fields.Char(related='picking_id.destination')
    box_nbr = fields.Integer(related='picking_id.box_nbr')
    new_parent_location = fields.Boolean('New Parent Location')
