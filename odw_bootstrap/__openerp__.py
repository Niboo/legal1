# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 DynApps <http://www.dynapps.be>
#
#    @author Peter Langenberg <peter.langenberg@dynapps.be>
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

{
    'name': 'Onderdelenwinkel database bootstrap',
    'version': '8.0.1.0.0',
    'depends': [
        'admin_technical_features',
        'account_accountant',
        'magentoerpconnect',
        ' xx_product_supplierinfo_tags',    
    ],
    'data': [
        'data/res_company.xml',
    ],
    'author': 'DynApps',
    'category': 'custom',
    'website': 'http://www.dynapps.be',
    'installable': True,
}
