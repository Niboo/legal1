{
    'name': 'Delay sales procurements when using just-in-time',
    'version': '1.0',
    'depends': [
        'procurement_jit',
        # Depend on purchase just to run full tests
        'purchase',
        'sale_stock',
        'procurement_jit_stock',
    ],
    'author': 'DynApps',
    'category': 'DynApps/Customizations',
    'website': 'http://www.dynapps.be',
    'installable': True,
}
