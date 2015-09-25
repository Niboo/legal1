# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Dynapps <http://www.dynapps.be>
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
    'name': 'Report to printer location - Easy Switch Work Location',
    'version': '1.0',
    'category': 'web',
    'description': """
Add menu to allow user to switch to another work location more easily
=====================================================================

Functionality:
--------------
    * Add a new menu in the top bar to switch to another work location more easily;
""",
    'depends': [
        'web',
        'dyn_report_to_printer_location',
    ],
    'data': [
        'view/res_users_view.xml',
    ],
    'js': [
        'static/src/js/switch_work_location.js',
    ],
    'qweb': [
        'static/src/xml/switch_work_location.xml',
    ],
    'installable': True,
    'auto_install': False,
}
