{
    "name": "Add purchase order CSV when emailing to suppliers",
    "version": "8.0.1.1",
    "depends": [
        "email_template",
        'purchase',
    ],
    'data': [
        'views/res_partner.xml',
        'views/purchase_order_view_inherit.xml',
        'wizard/display_csv_view.xml'
    ],
    "author": "DynApps",
    "category": "DynApps/Customizations",
    "website": "http://www.dynapps.be",
    "installable": True,
    "auto_install": False,
}
