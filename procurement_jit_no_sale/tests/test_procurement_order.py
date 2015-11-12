from openerp.tests import TransactionCase


class test_procurement_order(TransactionCase):
    def test_01_procurement_order(self):
        product = self.env['product.product'].create({
            'name': 'Name',
            'default_code': 'default_code',
            'type': 'product',
            'route_ids': [(4, self.env.ref('stock.route_warehouse0_mto'))],
            })
