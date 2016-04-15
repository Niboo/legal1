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

from openerp import models, api, fields


class ResUsers(models.Model):

    _inherit = "res.users"

    login_code = fields.Integer("Login code", default=-1)
    login_barcode = fields.Char("Login barcode")

    _sql_constraints = [
        ('login_code_secured',
         "CHECK(login_code > 1000 OR login_code = -1)",
         'This login code is not secured enough'),

        ('barcode_unique',
         'UNIQUE(login_barcode)',
         'The login barcode should be unique'),
    ]

    # def authenticate(self, db, login, password, user_agent_env):
    #     print "test"
    #     return super(ResUsers, self).authenticate(db, login, password, user_agent_env)
