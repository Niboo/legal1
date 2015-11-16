# -*- coding: utf-8 -*-
from openerp.tests import TransactionCase


class TestResetToDropshipment(TransactionCase):
    def setUp(self):
        super(TestResetToDropshipment, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Name',
            'default_code': 'default_code',
            'type': 'product',
            'sale_delay': 0,
            })
        self.product.route_ids += self.env.ref('stock.route_warehouse0_mto')

        supplier = self.env['res.partner'].create({
            'name':  'Supplier',
            'supplier': True})
        self.env['product.supplierinfo'].create({
            'name': supplier.id,
            'product_tmpl_id': self.product.product_tmpl_id.id})

    def test_01_sale_order(self):
        """ Test if a sale order can be successfully reset to dropshipment """
        customer = self.env['res.partner'].create({
            'name': 'Customer'})
        sale = self.env['sale.order'].create({
            'partner_id': customer.id,
            'order_policy': 'manual',
            'order_line': [(0, 0, {'product_id': self.product.id, })],
        })
        sale.action_button_confirm()
        self.assertEqual(sale.state, 'manual')
        procurement = sale.order_line.procurement_ids[0]
        self.assertEqual(procurement.state, 'confirmed')
        sale.reset_to_dropshipment()
        self.assertIn(
            self.env.ref('stock_dropshipping.route_drop_shipping'),
            procurement.route_ids)
        self.assertEqual(len(procurement.route_ids), 1)
        self.env['procurement.order'].run_scheduler(
            company_id=sale.company_id.id)
        self.assertEqual(procurement.state, 'running')
        self.assertTrue(procurement.purchase_id)
        self.assertEqual(
            procurement.purchase_id.picking_type_id,
            self.env.ref('stock_dropshipping.picking_type_dropship'))
