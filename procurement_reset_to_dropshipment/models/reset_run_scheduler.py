# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 DynApps <http://www.dynapps.be>
#
#    @author Stefan Rijnhart <stefan.rijnhart@dynapps.be>
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

import re
import logging
from datetime import datetime, timedelta
from os import listdir, unlink
from os.path import isfile, join, exists
from openerp import registry, models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError

logger = logging.getLogger(__name__)


class ResetRunScheduler(models.TransientModel):
    _name = 'reset.run.scheduler'

    @api.model
    def get_default_company_id(self):
        return self.env.user.company_id

    company_id = fields.Many2one(
        'res.company', default=get_default_company_id, required=True)
    notes = fields.Text(readonly=True)
    state = fields.Selection(
        [('init', 'Init'), ('run', 'Run')], default='init')
    no_reset = fields.Integer(readonly=True)
    grace_time = fields.Datetime(
        'Set procurements active from',
        default=lambda self: fields.Datetime.to_string(
            datetime.now() - timedelta(minutes=10)))

    @api.multi
    def fetch_magento_dropshipments(self):
        """ Fetch magento order files from a designated directory. After a lot
        of sanity checking, reset to dropshipment and delete the file. Try not
        to lose any information using aggressive logging and a dedicated cursor
        for the order reset.
        """
        self.notes = ''
        commit_cr = registry(self.env.cr.dbname).cursor()

        def log(msg, post=False, attachments=None):
            logger.info(msg)
            self.notes += msg + '\n'
            if post:
                post.message_post(body=msg, attachments=attachments)

        path = self.company_id.magento_dropship_path
        if not path:
            raise UserError(
                _('No directory defined on the company for dropship files '
                  'from Magento'))
        if not exists(path):
            raise UserError(
                _('The directory "%s" does not exist.') % path)

        if self.grace_time:
            self.env.cr.execute(
                """ UPDATE procurement_order SET active = true
                    WHERE active = false AND create_date < %s """,
                (fields.Datetime.from_string(self.grace_time),))

            log(_('%s procurements have been activated') % (
                self.env.cr.rowcount))

        files = [f for f in listdir(path) if isfile(join(path, f))]
        self.no_reset = 0
        for fi in files:
            match = re.search('([0-9]+)\.csv', fi)
            if not match:
                log(_('Unrecognized file name: %s, skipping') % fi)
                continue
            orderno = match.groups()[0]
            order = self.env['magento.orders'].search(
                [('mage_increment_id', '=', orderno)])
            if not order:
                log(_('No order found with magento order no. %s, '
                      'skipping %s') % (orderno, fi))
                continue
            if len(order) > 1:
                log(_('Multiple orders found with magento order no. %s, '
                      'that can\'t be right. Skipping %s') % (orderno, fi))
                continue
            if not order.order_ref:
                log(_('Magento order no. %s has no Odoo order. Skipping '
                      '%s') % (orderno, fi))
                continue
            sale = order.order_ref
            if sale.state not in (
                    'draft', 'sent', 'manual', 'progress', 'done'):
                log(_('Cannot reset Odoo order %s to dropshipment because '
                      'it is in state %s. Skipping %s') % (
                    sale.name, sale.state, fi), post=sale)
                continue
            if any(proc.state not in ('draft', 'confirmed') for proc in
                   sale.mapped('order_line').mapped('procurement_ids')):
                log(_('Cannot reset Odoo order %s to dropshipment because '
                      'it has a procurement that has already been processed. '
                      'Skipping %s') % (
                    sale.name, fi), post=sale)
                continue
            # Here we go
            with api.Environment.manage():
                env = api.Environment(
                    commit_cr, self.env.uid, self.env.context)
                try:
                    env['sale.order'].browse(sale.id).reset_to_dropshipment()
                    # TODO: add file as attachment to the sale order
                    commit_cr.commit()
                    file_loc = join(path, fi)
                    with file(file_loc) as f:
                        log(_('Magento order %s / Odoo order %s has been '
                              'reset to dropshipment') % (orderno, sale.name),
                            post=sale, attachments=[(fi, f.read())])
                    unlink(file_loc)
                    self.no_reset += 1
                except Exception, e:
                    log(_('Could not reset Odoo order %s to dropshipment: '
                        '%s. Skipping %s') % (sale.name, e, fi), post=sale)
                    commit_cr.rollback()

        commit_cr.close()
        self.state = 'run'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'reset.run.scheduler',
            'target': 'new',
            'view_mode': 'form',
            'res_id': self.id,
            }

    @api.multi
    def run_scheduler(self):
        self.env['procurement.order.compute.all'].procure_calculation()
