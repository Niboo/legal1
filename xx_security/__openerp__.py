{
    'name': 'Custom Security',
    'version': '1.0',
    'category': 'Security',
    'description': """
This module is used to change the standard security.
""",
    'author': 'DynApps',
    'website': 'http://www.dynapps.be',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        ],
    'installable': True,
    'auto_install': False,
}
