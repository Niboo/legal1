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


class InboundWave(models.Model):

    _name = "stock.inbound.wave"

    package_ids = fields.One2many('stock.quant.package', "inbound_wave_id", "Packages")
    user_id = fields.Many2one('res.users', 'User')
    state = fields.Selection([('new', 'New'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Done')], compute="_compute_state",
                             default='new', store=True)

    @api.multi
    @api.depends('package_ids.location_id')
    def _compute_state(self):
        bandup_locations = self.env['stock.location'].search([
            ('is_bandup_location', '=', True)
        ])

        for wave in self:
            if any(package.location_id.id in
                           bandup_locations.ids for package in wave.package_ids):
                if any(package.location_id and package.location_id.id not in
                               bandup_locations.ids for package in wave.package_ids):
                    wave.state = 'in_progress'
                else:
                    wave.state = 'new'
            else:
                wave.state = "done"
