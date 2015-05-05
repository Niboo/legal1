{
    "name": "Import Setup Data OW",
    "version": "1.0",
    "depends": [
        "base",
    ],
    "description": """
    Important
    =========
    DO not install this module unless you know what you are doing
    This module will import csv files for
        - stock location
        - product putaway strategy (header)
        - product putaway produclist (detail)
        - product supplierinfo
        - product supplier tags
        - product supplier info pricelines 
    """,
    "author": "DynApps",
    "category": "DynApps/Customizations",
    "website": "http://www.dynapps.be",
    "data": [
    ],
    'init': [
        'stock.location.csv',
        'product.putaway.csv',
        'stock.fixed.putaway.byprod.strat.csv',
        'product.supplierinfo.csv',
        'xx.product.supplierinfo.tags.csv',
        'pricelist.partnerinfo.csv',
    ],
    "installable": True,
    "auto_install": False,
}