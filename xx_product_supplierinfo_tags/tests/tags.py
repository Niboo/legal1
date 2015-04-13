from openerp.tests.common import TransactionCase
from openerp.osv import orm


class test_supplier_basic(TransactionCase):
	def setUp(self):
		super(test_tags_basic, self).setUp()
		self.product_supplierinfo_obj = self.registry('product_supplierinfo')
		self.stock_picking_obj = self.registry('stock_picking')
		self.product_product_obj = self.registry('product_product')
        self.usb_adapter_id = self.ir_model_data.get_object_reference(cr, uid, 'product', 'product_product_48')[1]
        self.datacard_id = self.ir_model_data.get_object_reference(cr, uid, 'product', 'product_product_46')[1]

	def test_10_check_fields(self):
		supplierinfo_cols = self.product_supplierinfo_obj.fields_get(self.cr, self.uid)
		self.assertIn('xx_tag_ids', supplierinfo_cols)

	def test_20_check_methods(self):
		self.assertTrue(hasattr(self.stock_picking_obj, 'process_barcode_from_ui'))
		self.assertTrue(hasattr(self.product_product, 'search'))

class test_supplier_info(TransactionCase):
	def setUp(self):
		super(test_supplier_info, self).setUp()
		self.product_supplierinfo_obj = self.registry('product_supplierinfo')
		self.stock_picking_obj = self.registry('stock_picking')
		self.product_product_obj = self.registry('product_product')

	def test_10_tag_update(self):
		cr, uid = self.cr, self.uid
