from openerp import models, fields


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    active = fields.Boolean(
        'Active', default=True, readonly=True,
        help=('Procurements from sale orders are set to inactive by default. '
              'When schedulers are run, all inactive procurements older than '
              'a small timespan are set to active. This allows us to work '
              'around a race condition between Magento and Odoo wrt. drop '
              'shipment.'))
