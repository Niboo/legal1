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

from openerp import models, fields, api, _
import time
from datetime import datetime


class PickingDispatch(models.Model):

    _inherit = 'picking.dispatch'

    start_time = fields.Datetime(string="Start Time",
                                 default=lambda self: datetime.now())

    end_time = fields.Datetime(String="End Time", default=False,
                               compute="_compute_time")

    total_time = fields.Float(String="Time Taken (hours)",
                              compute="_compute_time",
                              store=True)

    package_ids = fields.One2many('stock.quant.package',
                                  "picking_dispatch_id",
                                  "Packages")

    _sql_constraints = [
         ('end_time_correct',
         "CHECK(start_time <= end_time)",
         'Start time needs to be lower than End time')
    ]

    @api.depends("start_time", "end_time", "move_ids", "move_ids.state")
    @api.multi
    def _compute_time(self):
        for dispatch in self:

            dispatch.end_time = datetime.now()
            if dispatch.move_ids:
                if any(move.state != 'done' for move in dispatch.move_ids):
                    dispatch.end_time = False

            if dispatch.start_time and dispatch.end_time:
                start_time = dispatch.start_time
                end_time = dispatch.end_time

                start_time_obj = time.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                end_time_obj = time.strptime(end_time, "%Y-%m-%d %H:%M:%S")

                start_time_seconds = time.mktime(start_time_obj)
                end_time_seconds = time.mktime(end_time_obj)

                delta_seconds = end_time_seconds - start_time_seconds

                dispatch.total_time = delta_seconds / 3600

            else:
                dispatch.total_time = 0.0
