{
    "name": "Import Setup Data OW",
    "version": "1.0",
    "depends": [
        "xx_product_supplierinfo_tags",
        "putaway_apply",
    ],
    "description": """
        Do not install this module unless you know what you are doing
        This module uploads in BULK all the data in the csv files and this should only be done once.
        Before installing this module export first the WH location, else this module will give a traceback.
    """,
    "author": "DynApps",
    "category": "DynApps/Customizations",
    "website": "http://www.dynapps.be",
    "data": [
            'data/product.putaway.csv',
            'data/stock.fixed.putaway.byprod.strat.csv',
            'data/xx.product.supplierinfo.tags.csv',
            'data/product.supplierinfo.csv',
            'data/pricelist.partnerinfo.csv',
    ],
    'demo': [
    ],
    "installable": True,
    "auto_install": False,
}
