# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# Credits######################################################
#    Coded by:   Humberto Arocha humberto@openerp.com.ve
#                Angelica Barrios angelicaisabelb@gmail.com
#               Jordi Esteve <jesteve@zikzakmedia.com>
#               Javier Duran <javieredm@gmail.com>
#    Planified by: Humberto Arocha
#    Finance by: LUBCAN COL S.A.S http://www.lubcancol.com
#    Audited by: Humberto Arocha humberto@openerp.com.ve
#############################################################################
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
##############################################################################

import time
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv


class report_delivery_extended(report_sxw.rml_parse):

def get_client_order_ref(self,name):
        res = ''
        if name not in  self.sale_order :
            sale_order_id=self.pool.get("sale.order").search(self.cr,self.uid,[('name','=',name)])
            sale_obj=self.pool.get("sale.order").browse(self.cr,self.uid,sale_order_id,context=None)
            res =''
            if sale_obj:
                res = sale_obj.client_order_ref  or ""
                res += ' ' + sale_obj.partner_id.name
                if sale_obj.partner_id.city:
                    res += ' '+ sale_obj.partner_id.city
        return res
