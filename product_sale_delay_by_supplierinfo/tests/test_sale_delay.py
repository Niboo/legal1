# -*- coding: utf-8 -*-
from openerp.tests import TransactionCase


class TestSaleDelay(TransactionCase):
    def setUp(self):
        super(TestSaleDelay, self).setUp()
        self.template = self.env['product.template'].create({
            'name': 'Name',
            'default_code': 'default_code',
            'type': 'product',
            'sale_delay': 7,
        })

    def test_01_sale_delay(self):
        info = self.env['product.supplierinfo'].create({
            'name': self.env['res.partner'].search(
                [('supplier', '=', True)], limit=1).id,
            'delay': 2,
            'min_qty': 1,
            'sequence': 5,
            'product_tmpl_id': self.template.id,
        })
        self.assertEqual(self.template.sale_delay, 3)
        info.write({'delay': 3})
        self.assertEqual(self.template.sale_delay, 4)
        info2 = self.env['product.supplierinfo'].create({
            'name': self.env['res.partner'].search(
                [('supplier', '=', True)], offset=1, limit=1).id,
            'delay': 4,
            'min_qty': 1,
            'sequence': 10,
            'product_tmpl_id': self.template.id,
        })
        self.assertEqual(self.template.sale_delay, 4)
        info2.write({'sequence': 4})
        self.assertEqual(self.template.sale_delay, 5)
