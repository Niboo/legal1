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
    'name': 'Dynapps Kanban Sanity',
    'version': '8.0.1.0.0',
    'category': 'Uncategorised',
    'description': """
This module removes the following dangerous Kanban options from project.task:

* Delete (on column): prevents accidental orphaning of items not shown in current view
* Edit (on column): for consistency
* Add a new column (next to Create): for consistency

The use case for this is the tasks view in the project module, where a user
can delete stages they don't need in their projects. Users don't always
realise this has impact outside of their own projects.

By removing these buttons we force the user to go through the Stages config
screens, where it's more obvious that this can impact more than just their own
projects.

Furthermore, we set a constraint on stage_id so that stages can not be deleted
unless no tasks link to it.
    """,
    'author': 'Dynapps',
    'website': 'http://www.dynapps.be/',
    'license': 'AGPL-3',
    'depends': ['project'],
    'data': [
        'views/project_task.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'images': [],
    'css': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
