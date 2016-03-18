# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Jerome Guerriat
#    Copyright 2015 Niboo SPRL
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import http
from openerp import exceptions


class InboundController(http.Controller):
    @http.route('/inbound_screen', type='http', auth="user")
    def inbound_screen(self, **kw):
        inbound_suppliers  = http.request.env['res.partner'].search(
            [('is_in_inbound','=',True)]
            ,order='sequence'
        )

        return http.request.render('stock_irm.inbound_screen', {
              'suppliers': inbound_suppliers,
        })

    @http.route('/inbound_screen/get_suppliers_data', type='json', auth="user")
    def get_suppliers_data(self, search="",  **kw):
        env = http.request.env
        inbound_suppliers = list()

        domain = [('is_in_inbound','=',True)]

        if search:
            domain.append(('display_name','ilike',search))

        suppliers = env['res.partner'].search(
            domain,
            order='sequence'
        )

        for supplier in suppliers:
            inbound_suppliers.append({
                'name': supplier.name,
                'image': "/web/binary/image?model=res.partner&id=%s&field=image" % supplier.id
            })
        results = {'status': 'ok',
                   'suppliers': inbound_suppliers}
        return results

    @http.route('/inbound_screen/get_products_data', type='json', auth="user")
    def get_products_data(self, search="", page=0,  **kw):
        cr = http.request.cr
        env = http.request.env
        products = list()

        if not search:
            raise exceptions.ValidationError('You have to specify at least one character')

        search_limit = 30
        search_offset = page * search_limit

        search = '%%%s%%' % search

        cr.execute("""SELECT pp.id, pt.name FROM product_template AS pt
JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
WHERE name ilike %s AND sale_ok IS TRUE
ORDER BY pp.id
LIMIT %s
OFFSET %s
""", [search, search_limit, search_offset])
        products_results = cr.fetchall()

        cr.execute("""SELECT count(*) FROM product_template AS pt
JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
WHERE name ilike %s AND sale_ok IS TRUE
""", [search])

        products_count = cr.fetchall()

        for product in products_results:
            products.append({
                'name': product[1],
                'image': "/web/binary/image?model=product.product&id=%s&field=image" % product[0]
            })

        results = {'status': 'ok',
                   'products': products,
                   'products_count': products_count[0]}

        return results