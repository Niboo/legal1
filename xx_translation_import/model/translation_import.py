
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from openerp.osv import osv, fields
import time
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import logging

import openerp.modules as addons
from openerp import pooler
from openerp import tools

_logger = logging.getLogger(__name__)

class translation_import(osv.osv_memory):
    _name = 'xx.translation.import'
    _description = 'Translation importer'
    
    _columns = {
        'custom_location': fields.char('Custom Location', size=128),
        'remember_location': fields.boolean('Remember location'),
        'property_custom_location_remembered': fields.property(
            type='char', 
            size=128,
            domain=[],
            string="Custom location remembered",
            view_load=True),
    }
    
    _defaults = {
        'remember_location': False
    }
    
    def default_get(self, cr, uid, fields, context=None):
        values = super(translation_import, self).default_get(cr, uid, fields, context=context)
        
        try:
            values['custom_location'] = self.pool.get('ir.property').get(cr, uid,
                'property_custom_location_remembered', 'xx.translation.import')
        except:
            pass
        
        values['remember_location'] = (values.get('custom_location', False) and True or False)
        
        return values

    def check_property(self, cr, uid, custom_location, remember_location):
        property_obj = self.pool.get('ir.property')
        user_obj = self.pool.get('res.users')
        fields_obj = self.pool.get('ir.model.fields')
        
        company_id = user_obj.browse(cr, uid, uid).company_id.id
        
        if remember_location:
            property_ids = property_obj.search(cr, uid, [('name', '=', 'property_custom_location_remembered'), 
                    ('company_id', '=', company_id)])
            
            field_ids = fields_obj.search(cr, uid, [('model', '=', 'xx.translation.import'), 
                    ('name', '=', 'property_custom_location_remembered')])
                    
            values = {
                'name':'property_custom_location_remembered', 
                'value':custom_location, 
                'type':'char', 
                'fields_id':field_ids[0], 
                'company_id':company_id}
            
            if len(property_ids) == 0:
                property_obj.create(cr, uid, values)
            else:
                property_obj.write(cr, uid, property_ids, values)

    def do_import_translations(self, cr, uid, ids, context=None):
        for import_values in self.browse(cr, uid, ids):
            custom_location = import_values.custom_location
            remember_location = import_values.remember_location
            
            if not custom_location:
                return {}
            
            self.check_property(cr, uid, custom_location, remember_location)
                
            self.update_translations(cr, uid, ids, custom_location)
            # Do the actual import
            return {}
        
    def update_translations(self, cr, uid, ids, custom_location, filter_lang=None, context=None):
        if context is None:
            context = {}
        if not filter_lang:
            pool = pooler.get_pool(cr.dbname)
            lang_obj = pool.get('res.lang')
            lang_ids = lang_obj.search(cr, uid, [('translatable', '=', True)])
            filter_lang = [lang.code for lang in lang_obj.browse(cr, uid, lang_ids)]
        elif not isinstance(filter_lang, (list, tuple)):
            filter_lang = [filter_lang]
        
        # always overwrite
        context['overwrite'] = True
            
        module_obj = self.pool.get('ir.module.module')
        module_ids = module_obj.search(cr, uid, [('state', '=', 'installed')])

        for mod in module_obj.browse(cr, uid, module_ids):
            if mod.state != 'installed':
                continue
            modpath = addons.get_module_path(mod.name)
            
            if not modpath:
                continue
            # only overwrite modules within this path location
            if not custom_location in modpath:
                continue            

            for lang in filter_lang:
                iso_lang = tools.get_iso_codes(lang)
                f = addons.get_module_resource(mod.name, 'i18n', iso_lang + '.po')
                context2 = context and context.copy() or {}
                if f and '_' in iso_lang:
                    iso_lang2 = iso_lang.split('_')[0]
                    f2 = addons.get_module_resource(mod.name, 'i18n', iso_lang2 + '.po')
                    if f2:
                        _logger.info('module %s: loading base translation file %s for language %s', mod.name, iso_lang2, lang)
                        tools.trans_load(cr, f2, lang, verbose=False, context=context)
                        context2['overwrite'] = True
                # Implementation notice: we must first search for the full name of
                # the language derivative, like "en_UK", and then the generic,
                # like "en".
                if (not f) and '_' in iso_lang:
                    iso_lang = iso_lang.split('_')[0]
                    f = addons.get_module_resource(mod.name, 'i18n', iso_lang + '.po')
                if f:
                    _logger.info('module %s: loading translation file (%s) for language %s', mod.name, iso_lang, lang)
                    tools.trans_load(cr, f, lang, verbose=False, context=context2)
                elif iso_lang != 'en':
                    _logger.warning('module %s: no translation for language %s', mod.name, iso_lang)
        
        