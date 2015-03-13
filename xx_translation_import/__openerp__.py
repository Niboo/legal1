{
    "name": "Translation Importer",
    "version": "1.0",
    "depends": ["base"],
    "description": "Makes it possible for a user to reload translations from the custom modules",
    "author": "DynApps",
    "category": "",
    "website": "http://www.dynapps.be",
    "init_xml": [
    ],
    "update_xml": [
        "view/translation_import.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True,
    "auto_install": False,
}
