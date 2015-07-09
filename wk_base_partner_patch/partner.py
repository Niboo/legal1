 # -*- coding: utf-8 -*-
##############################################################################
#		
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################


from openerp.osv import osv,fields


class res_partner(osv.osv):
	_inherit = 'res.partner'

	def name_get(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		if isinstance(ids, (int, long)):
			ids = [ids]
		res = []
		for record in self.browse(cr, uid, ids, context=context):
			name = record.name
			if record.parent_id and not record.is_company and record.parent_id.is_company:
				name =  "%s, %s" % (record.parent_id.name, name)
			if context.get('show_address'):
				name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
				name = name.replace('\n\n','\n')
				name = name.replace('\n\n','\n')
			if context.get('show_email') and record.email:
				name = "%s <%s>" % (name, record.email)
			res.append((record.id, name))
		return res

	def _display_address(self, cr, uid, address, without_company=False, context=None):

		'''
		The purpose of this function is to build and return an address formatted accordingly to the
		standards of the country where it belongs.

		:param address: browse record of the res.partner to format
		:returns: the address formatted in a display that fit its country habits (or the default ones
		    if not country is specified)
		:rtype: string
		'''

		# get the information that will be injected into the display format
		# get the address format
		if address.country_id and address.country_id.address_format:
			address_format = "%(wk_company)s\n"+address.country_id.address_format
		else:
			address_format = "%(wk_company)s\n%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
		args = {
		    'wk_company': address.wk_company or '',
		    'state_code': address.state_id and address.state_id.code or '',
		    'state_name': address.state_id and address.state_id.name or '',
		    'country_code': address.country_id and address.country_id.code or '',
		    'country_name': address.country_id and address.country_id.name or '',
		    'company_name': address.parent_id.is_company and address.parent_id and address.parent_id.name or '',
		}
		for field in self._address_fields(cr, uid, context=context):
			args[field] = getattr(address, field) or ''
		if without_company:
			args['company_name'] = ''
		elif address.parent_id:
			address_format = '%(company_name)s\n' + address_format
		res = address_format % args
		if res and "\n\n" in res:
			res = res.replace('\n\n', '\n')
		return res
		
	_columns = {
		'wk_address': fields.boolean('Address'),
		'wk_company': fields.char('Company', size=128),
	}