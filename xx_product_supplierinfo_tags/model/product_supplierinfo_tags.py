# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DynApps (<http://www.dynapps.be>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields

class product_supplierinfo_tags(models.Model):
    _name = "xx.product.supplierinfo.tags"
    _inherit = "xx.tags"

class product_supplierinfo(models.Model):
    _name = "product.supplierinfo"
    _inherit = "product.supplierinfo"

    xx_tag_ids = fields.One2many('xx.product.supplierinfo.tags', 'res_id', string='Supplier Barcodes', domain=[('res_model', '=', _name)])

class stock_picking(models.Model):
    _inherit = "stock.picking"

    def process_barcode_from_ui(self, cr, uid, picking_id, barcode_str, visible_op_ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({
            "process_barcode_from_ui_picking_id": picking_id,
            "process_barcode_from_ui_barcode_str": barcode_str,
        })
        return super(stock_picking, self).process_barcode_from_ui(cr, uid, picking_id, barcode_str, visible_op_ids, context=ctx)

class product_product(models.Model):
    _inherit = 'product.product'

    def search(self, cr, uid, search_args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        ctx = context.copy()
        product_ids = super(product_product, self).search(cr, uid, search_args, offset=offset, limit=limit, order=order, context=ctx, count=count)
        if 'process_barcode_from_ui_picking_id' in ctx:
            sp = self.pool.get('stock.picking').browse(cr,uid,[ctx.get('process_barcode_from_ui_picking_id')], context=context)[0]
            if sp.picking_type_id.code == 'incoming':
                cr.execute("""
                SELECT pp.id
                FROM stock_picking sp
                    INNER JOIN product_supplierinfo ps ON ps.name = sp.partner_id
                    INNER JOIN xx_product_supplierinfo_tags xpst ON xpst.res_id = ps.id
                                                                AND xpst.res_model = 'product.supplierinfo'
                                                                AND xpst.name like '%%%(needle)s%%'
                    INNER JOIN product_product pp ON pp.product_tmpl_id = ps.product_tmpl_id
                    INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE sp.id = %(p_id)s AND pt.company_id = sp.company_id
                UNION
                SELECT pp.id
                FROM stock_picking sp
                    INNER JOIN product_supplierinfo ps ON ps.name = sp.partner_id
                    INNER JOIN product_product pp ON pp.product_tmpl_id = ps.product_tmpl_id
                    INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE sp.id = %(p_id)s  AND pt.company_id = sp.company_id AND ps.product_code ilike '%%%(needle)s%%'
                UNION
                SELECT pp.id
                FROM stock_picking sp
                    INNER JOIN product_supplierinfo ps ON ps.name = sp.partner_id
                    INNER JOIN product_product pp ON pp.product_tmpl_id = ps.product_tmpl_id
                    INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE sp.id = %(p_id)s  AND pt.company_id = sp.company_id AND pt.manufacturer_pref ilike '%%%(needle)s%%'
                UNION
                SELECT pp.id
                FROM stock_picking sp
                    INNER JOIN product_supplierinfo ps ON ps.name = sp.partner_id
                    INNER JOIN product_product pp ON pp.product_tmpl_id = ps.product_tmpl_id
                    INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE sp.id = %(p_id)s  AND pt.company_id = sp.company_id AND (
                            pp.ean13 ilike '%%%(needle)s%%' OR
                            pp.default_code ilike '%%%(needle)s%%'
                        )
                """ % {'needle':ctx.get('process_barcode_from_ui_barcode_str'), 'p_id':ctx.get('process_barcode_from_ui_picking_id')})
                query_result = cr.fetchall()
                product_ids = ([x[0] for x in query_result])
            else:
                cr.execute("""
                SELECT pp.id
                FROM stock_picking sp
                    INNER JOIN product_supplierinfo ps ON ps.name = sp.partner_id
                    INNER JOIN product_product pp ON pp.product_tmpl_id = ps.product_tmpl_id
                    INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE sp.id = %(p_id)s  AND pt.company_id = sp.company_id AND (
                            pp.ean13 ilike '%%%(needle)s%%' OR
                            pp.default_code ilike '%%%(needle)s%%'
                        )
                """ % {'needle':ctx.get('process_barcode_from_ui_barcode_str'), 'p_id':ctx.get('process_barcode_from_ui_picking_id')})
                query_result = cr.fetchall()
                product_ids = [x[0] for x in query_result]

        else:
            for arg in search_args:
                if arg[0] in ['name','default_code']:
                    cr.execute("""
                    SELECT DISTINCT pp.id
                    FROM product_product pp
                        LEFT JOIN product_supplierinfo psi
                            ON psi.product_tmpl_id = pp.product_tmpl_id
                        LEFT JOIN xx_product_supplierinfo_tags psit
                            ON psit.res_id = psi.id AND psit.res_model like 'product.supplierinfo'
                        INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    WHERE
                        pt.company_id = {comp} AND (
                        pp.name_template ilike '%%{needle}%%' OR
                        pp.default_code ilike '%%{needle}%%' OR
                        pp.ean13 ilike '%%{needle}%%' OR
                        psi.product_code ilike '%%{needle}%%' OR
                        psit.name ilike '%%{needle}%%')
                    """.format(needle=arg[2].strip(),
                        comp=self.pool.get('res.users').browse(cr,uid,[uid],context=context)[0].company_id.id))
                    query_result = cr.fetchall()
                    product_ids += [x[0] for x in query_result]
        return product_ids
