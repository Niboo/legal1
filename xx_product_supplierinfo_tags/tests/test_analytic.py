from openerp.tests import TransactionCase


class test_base_supplier_info(TransactionCase):
    def test_10_model(self):
        model = self.env['product.supplierinfo']
        fields = model.fields_get().keys()
        self.assertIn('name', fields)
        self.assertIn('xx_tag_ids', fields)

    def test_20_view(self):
        model = self.env['product.supplierinfo']
        view = model.fields_view_get(False, 'form')
        fields = view['fields'].keys()
        self.assertIn('name', fields)
        self.assertIn('xx_tag_ids', fields)

class test_base_supplier_info_tags(TransactionCase):
    def test_10_model(self):
        """ Check  fields on tag model. """
        model = self.env['xx.product.supplierinfo.tags']
        fields = model.fields_get().keys()
        self.assertIn('name', fields)
        self.assertIn('res_model', fields)
        self.assertIn('res_id', fields)

class test_function(TransactionCase):
    def test_10_index(self):
        """ Check functions on product_supplierinfo. """
        model = self.env['xx.product.supplierinfo.tags']

        r_id = self.ref("product.product_supplierinfo_1")
        model1000 = model.create({
            'name': 'xx_1000',
            'res_model': 'product.supplierinfo',
            'res_id': r_id,
        })
        self.assertEqual(model1000.name, 'xx_1000')
        model1001 = model.create({
            'name': 'xx_1001',
            'res_model': 'product.supplierinfo',
            'res_id': r_id,
        })
        self.assertEqual(model1001.name, 'xx_1001')
        model1002 = model.create({
            'name': 'xx_1002',
            'res_model': 'product.supplierinfo',
            'res_id': r_id,
        })
        self.assertEqual(model1002.name, 'xx_1002')

        self.ProductObj = self.env['product.product']
        self.productA = self.ProductObj.create({'name': 'Product A'})
        self.productB = self.ProductObj.create({'name': 'Product B'})
        self.productC = self.ProductObj.create({'name': 'Product C'})
        self.productD = self.ProductObj.create({'name': 'Product D'})
        self.PartnerObj = self.env['res.partner']
        self.Supplier1 = self.PartnerObj.create({'name': 'Supplier 1'})

        # Create supplier info
        product_supplierinfo_obj = self.env['product.supplierinfo']
        supplierinfo = product_supplierinfo_obj.create({
            'name': self.Supplier1.id,
            'product_tmpl_id': self.productA.product_tmpl_id.id,
            'product_name': 'Voorbeeld',
            'xx_tag_ids': [(6,0,[model1000.id,model1001.id,model1002.id])]
        })

        # Test on seach product via barcode
        product_product_obj = self.env['product.product']
        import pdb; pdb.set_trace()
        f_id = product_product_obj.search([('name','=','xx_1000')])
        self.assertEqual(f_id[0].id, self.productA.id)

