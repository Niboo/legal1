from openerp.tests import TransactionCase

class test_function(TransactionCase):
    def test_10_index(self):
        """ Check if template(s) exist. """
        self.EmailObj = self.env['email.template']
        f_id = self.EmailObj.search([('id','in',[ref('email_beekman'),ref('email_vedelec'),ref('email_aswo')])
        self.assertEqual(len(f_ids), 3,"csv beekman-vedelect-aswo templates export missing")



