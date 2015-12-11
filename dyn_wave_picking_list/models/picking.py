# -*- coding: utf-8 -*-
from openerp import fields, models, api


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    packages_assigned = fields.Boolean(
        'Packages Have Been Assigned', required=False)
    box_nbr = fields.Integer('Box #')
    wave_info = fields.Text(compute="_get_wave_info")
    # Destination field is used in the picking report when printed from the
    # wave form (but only updated after printing the wave)
    destination = fields.Char()

    @api.multi
    def _get_wave_info(self):
        for picking in self:
            infos = []
            if picking.name:
                infos.append(picking.name)
            if picking.group_id:
                if picking.group_id.name not in infos:
                    infos.append(picking.group_id.name)
                for sale in self.env['sale.order'].search(
                        [('procurement_group_id', '=', picking.group_id.id)]):
                    if sale.client_order_ref and sale.client_order_ref not in infos:
                        infos.append(sale.client_order_ref)
            picking.wave_info = '\n'.join(infos)
