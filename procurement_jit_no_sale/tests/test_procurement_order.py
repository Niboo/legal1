# -*- coding: utf-8 -*-
from openerp.tests import TransactionCase
from openerp import pooler


class TestProcurementOrder(TransactionCase):
    def setUp(self):
        super(TestProcurementOrder, self).setUp()
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
        warehouse = (
            self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.user.company_id.id)]) or
            self.env['stock.warehouse'].search(
                [('company_id', '=', False)]))
        self.procurement_vals = {
            'product_id': self.product.id,
            'product_qty': 1,
            'name': 'Procurement',
            'warehouse_id': warehouse.id,
            'location_id': warehouse.lot_stock_id.id,
            'route_ids': [(6, 0, self.product.route_ids.ids)],
        }
        self.procurement_vals.update(
            self.env['procurement.order'].onchange_product_id(
                self.product.id)['value'])

    def test_02_sale_order(self):
        """ Check that a sales procurement does not run except when the \
scheduler is run """
        customer = self.env['res.partner'].create({
            'name': 'Customer'})
        sale = self.env['sale.order'].create({
            'partner_id': customer.id,
            'order_policy': 'manual',
            'order_line': [(0, 0, {'product_id': self.product.id, })],
        })
        sale.action_button_confirm()
        self.assertEqual(sale.state, 'manual')
        self.assertEqual(sale.order_line.procurement_ids.state, 'confirmed')
        self.env['procurement.order'].run_scheduler(
            company_id=sale.company_id.id)
        self.assertEqual(sale.order_line.procurement_ids.state, 'running')
        procurements = sale.order_line.procurement_ids
        while procurements:
            procurement = procurements[0]
            if not procurement.move_ids:
                break
            procurements = self.env['procurement.order'].search(
                [('move_dest_id', '=', procurement.move_ids[0].id)])
        self.assertTrue(procurement.purchase_id)

    def test_00_procurement_old_api(self):
        """ Check that we can create an old API procurement.
        Monkey patching across APIs was not entirely obvious """
        pool = pooler.get_pool(self.env.cr.dbname)
        proc_model = pool['procurement.order']
        procurement_id = proc_model.create(
            self.env.cr, self.env.uid, self.procurement_vals,
            context=self.env.context)
        print procurement_id
        self.assertIsInstance(procurement_id, (int, long))

    def test_01_procurement_new_api(self):
        """ Check that we can create a new API procurement, which is \
processed automatically """
        procurements = self.env['procurement.order'].create(
            self.procurement_vals)
        self.assertEqual(procurements[0].state, 'running')
        while procurements:
            procurement = procurements[0]
            if not procurement.move_ids:
                break
            procurements = self.env['procurement.order'].search(
                [('move_dest_id', '=', procurement.move_ids[0].id)])
        self.assertTrue(procurement.purchase_id)
