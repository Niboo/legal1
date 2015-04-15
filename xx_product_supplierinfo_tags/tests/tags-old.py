from openerp.tests import TransactionCase


class test_base_invoice_index(TransactionCase):
    def test_10_model(self):
        model = self.env['product.product_supplierinfo']
        fields = model.fields_get().keys()
        self.assertIn('name', fields)


# from openerp.tests import TransactionCase


# class test_base_supplierinfo(TransactionCase):
#     def test_10_model(self):
#         """ Check new fields on supplierinfo model. """
#         model = self.env['product.product_supplierinfo']
#         fields = model.fields_get().keys()
#         self.assertIn('name', fields)
#         self.assertIn('kieken', fields)
#         self.assertIn('xx_tag_ids', fields)

#     def test_20_view(self):
#         """ Check  fields on view supplierinfo model. """
#         model = self.env['product.product_supplierinfo']
#         view = model.fields_view_get(False, 'form')
#         fields = view['fields'].keys()
#         self.assertIn('product_tmpl_id', fields)
#         self.assertIn('xx_tag_ids', fields)

# class test_base_supplier_info_tags(TransactionCase):
#     def test_10_model(self):
#         """ Check  fields on tag model. """
#         model = self.env['xx.product.supplierinfo.tags']
#         fields = model.fields_get().keys()
#         self.assertIn('name', fields)
#         self.assertIn('model', fields)
#         self.assertIn('res_id', fields)


# class test_function(TransactionCase):
#     def test_10_index(self):
#         """ Check functions on product_supplierinfo. """
#         model = self.env['xx_product_supplierinfo_tags']

#         model1000 = model.create({
#             'name': '1000',
#             'res_model': 'product.supplierinfo',
#             'res_id': ref("product.product_supplierinfo_1"),
#         })
#         self.assertEqual(model1000.name, '1002')
#         model1001 = model.create({
#             'name': '1001',
#             'res_model': 'product.supplierinfo',
#             'res_id': ref("product.product_supplierinfo_1"),
#         })
#         model1002 = model.create({
#             'name': '1002',
#             'res_model': 'product.supplierinfo',
#             'res_id': ref("product.product_supplierinfo_1"),
#         })

#         # Create supplier info
#         product_supplierinfo = self.env['product_supplierinfo']
#         supplierinfo = product_supplierinfo.write({
#             'product_name': 'Voorbeeld',
#             'xx_tag_ids': [(6,0,[model1000,model1001,model1002])]
#         })
