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
        company_id1 = self.ref('base.main_company')
        #create company 2
        self.CompanyObj = self.env['res.company']
        self.company2 = self.CompanyObj.create({'name': 'test company A'})
        company_id2 = self.company2.id
        
        model = self.env['xx.product.supplierinfo.tags']

        r_id = self.ref("product.product_supplierinfo_1")
        model1000 = model.create({
            'name': 'xx_1000',
            'res_model': 'product.supplierinfo',
            'res_id': r_id,
        })
        r_id = self.ref("product.product_supplierinfo_1")
        model1000_2 = model.create({
            'name': 'xx_1000',
            'res_model': 'product.supplierinfo',
            'res_id': r_id,
        })
        self.assertEqual(model1000_2.name, 'xx_1000')
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
        self.productA = self.ProductObj.create({'name': 'Product A','default_code': 'B123456', 'company_id': company_id1})
        self.productB = self.ProductObj.create({'name': 'Product B','default_code': 'B123456', 'company_id': company_id2})
        self.productC = self.ProductObj.create({'name': 'Product C','default_code': 'C123456', 'company_id': company_id1})
        self.productD = self.ProductObj.create({'name': 'Product D','default_code': 'D123456',  'company_id': company_id1})
        self.PartnerObj = self.env['res.partner']
        self.Supplier1 = self.PartnerObj.create({'name': 'Supplier 1'})
        self.Supplier2 = self.PartnerObj.create({'name': 'Supplier 2'})
        self.Customer1 = self.PartnerObj.create({'name': 'Customer 1'})
        self.Customer2 = self.PartnerObj.create({'name': 'Customer 2'})

        # Create supplier info
        product_supplierinfo_obj = self.env['product.supplierinfo']
        supplierinfo = product_supplierinfo_obj.create({
            'name': self.Supplier1.id,
            'product_tmpl_id': self.productA.product_tmpl_id.id,
            'product_name': 'Voorbeeld',
            'xx_tag_ids': [(6,0,[model1000.id,model1001.id,model1002.id])]
        })

        # Test on search product via barcode -- company1
        self.product_product_obj = self.env['product.product']
        self.PickingObj = self.env['stock.picking']
        self.PickingtypeObj = self.env['ir.model.data']
        #create an outgoing picking order
        self.picking_type_in = self.PickingtypeObj.xmlid_to_res_id('stock.picking_type_in')
        picking_in = self.PickingObj.create({
            'partner_id': self.Supplier1.id,
            'picking_type_id': self.picking_type_in})


#incoming picking
# test with standard odoo client
        context = {}

        f_id = self.product_product_obj.search([('name','=','xx_1000'),('company_id','=', company_id1)])
        self.assertEqual(len(f_id),2,"should find 2 results")
        self.assertEqual(f_id[0].id, self.productA.id,"1 Product with name xx_1000 should exist in main company")
        #
        # f_id = self.product_product_obj.search([('name','=','xx_1000'),('company_id',"=", company_id2)],context=context)
        # self.assertEqual(len(f_id),0,"This search must give no results because product is in other company")

        f_id = self.product_product_obj.search([('name','=','Product B'),('company_id','=', company_id1)])
        self.assertEqual(f_id[0].id, self.productB.id)

        f_id = self.product_product_obj.search([('default_code','=','C123456'),('company_id','=', company_id1)],context=context)
        self.assertEqual(f_id[0].id, self.productC.id)

# test barcode client - type incoming
        prod = self.env['product.product'].with_context({'process_barcode_from_ui_barcode_str': 'xx_1000','process_barcode_from_ui_picking_id': picking_in.id })
        f_id = prod.search([('name','=','xx_1000'),('company_id','=', company_id1)])
        self.assertEqual(len(f_id),1,"should find 1 result")
        self.assertEqual(f_id[0].id, self.productA.id,"2 Product with name xx_1000 should exist in main company")
        #
        # f_id = self.product_product_obj.search([('name','=','xx_1000'),('company_id',"=", company_id2)],context=context)
        # self.assertEqual(len(f_id),0,"This search must give no results because product is in other company")

        f_id = self.product_product_obj.search([('name','=','Product B'),('company_id','=', company_id1)],context=context)
        self.assertEqual(f_id[0].id, self.productB.id)

        f_id = self.product_product_obj.search([('default_code','=','C123456'),('company_id','=', company_id1)],context=context)
        self.assertEqual(f_id[0].id, self.productC.id)

#outgoing picking
        self.picking_type_out = self.PickingtypeObj.xmlid_to_res_id('stock.picking_type_out')
        picking_out = self.PickingObj.create({
            'partner_id': self.Customer1.id,
            'picking_type_id': self.picking_type_out})
        context = {'process_barcode_from_ui_barcode_str': '','process_barcode_from_ui_picking_id': picking_out.id }

        f_id = self.product_product_obj.search([('name','=','xx_1000'),('company_id','=', company_id1)],context=context)
        self.assertEqual(f_id[0].id, self.productA.id,"3 Product with name xx_1000 should exist in main company")
        #
        # f_id = self.product_product_obj.search([('name','=','xx_1000'),('company_id',"=", company_id2)],context=context)
        # self.assertEqual(len(f_id),0,"This search must give no results because product is in other company")

        f_id = self.product_product_obj.search([('name','=','Product B'),('company_id','=', company_id1)],context=context)
        self.assertEqual(f_id[0].id, self.productB.id)

        f_id = self.product_product_obj.search([('default_code','=','C123456'),('company_id','=', company_id1)],context=context)
        self.assertEqual(f_id[0].id, self.productC.id)



