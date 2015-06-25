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
        In batch mode : 
        login in op de staging server (of ooit eenmalig op de productieserver)
        cd /etc/init
        stop odoo-owodoost (indien het de productieserver is -> odoo-owodoo)
        python /data/vhosts/odoo-staging.onderdelenwinkel.nl/odoo/odoo.py --addons-path=/data/vhosts/odoo-staging.onderdelenwinkel.nl/odoo/openerp/addons,/data/vhosts/odoo-staging.onderdelenwinkel.nl/odoo/addons,/data/vhosts/odoo-staging.onderdelenwinkel.nl/custom -i xx_import_ow --stop-after-init
        Als het script is beeindigd
	login again
        cd /etc/init
	start odoo-owodoost (indien het productiesrever is -> odoo-owodoo)
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
    "installable": False,
    "auto_install": False,
}
