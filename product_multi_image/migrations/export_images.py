#!/usr/bin/env python
#nog te maken.
import xmlrpclib
import csv
import logging
import time
import sys
import ConfigParser
import os.path
import os

csv.field_size_limit(sys.maxsize)

directory = 'logs'
if not os.path.exists(directory):
    print 'create new log folder'
    os.makedirs(directory)

logger = logging.getLogger('import_images')
hdlr = logging.FileHandler('logs/import.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.WARNING)

def read_config():
    Config = ConfigParser.ConfigParser()
    teller = 0
    while len(Config.read("import.conf")) == 0 or teller > 3:
        teller += 1
        # lets create that config file for next time...
        cfgfile = open("import.conf",'w')
        # add the settings to the structure of the file, and lets write it out...
        Config.add_section('config')
        Config.set('config','url','https://')
        Config.set('config','dbname', 'database')
        Config.set('config','user', 'admin')
        Config.set('config','pwd', 'passwoord')
        Config.add_section('import')
        Config.write(cfgfile)
        cfgfile.close()
        print 'import.conf file bestond niet, lege gemaakt, gelieve te configureren'
        sys.exit()
    if teller > 3:
        print "probleem met de config file"
        sys.exit()
    print 'conf file ingelezen'
    convert = {}
    convert['url'] = Config.get("config",'url')
    convert['dbname'] = Config.get("config",'dbname')
    convert['user'] = Config.get("config",'user')
    convert['pwd'] = Config.get('config','pwd')
    return convert

def convert(config):
    '''
    '''
    try:
        l = xmlrpclib.Server("{}/xmlrpc/2/common".format(config['url']))
        config['uid'] = l.login(config['dbname'], config['user'], config['pwd'])
    except Exception, fboodschap:
        print 'url : %s' % config['url']
        print 'dbname : %s ' % config['dbname']
        print 'user : %s ' % config['user']
        print 'password : %s ' % config['pwd']
        raise fboodschap


    s = xmlrpclib.Server("{}/xmlrpc/2/object".format(config['url']))
    e = lambda *a: s.execute(config['dbname'], config['uid'], config['pwd'], *a)

    process_start_time = time.time()
    logger.warning("**** start export program : %s" % (process_start_time))
    logger.warning("succes creating sockets")
    logger.warning("csvfile %s " % "csvfiles/odoo_import_images.csv")
    logger.warning("**** start export images")
    print 'start export'
    start_time = time.time()
    export_product_images(e)
    logger.warning("**** stop export images, time used %s" % (time.time() - start_time))

    logger.warning("**** end export program : %s" % (time.time() - process_start_time))
    print 'please consult the export.log file'

def export_product_images(e):
    t = 0
    # layout file -> "external xml-id", active, comment,
    # "xml-id van de company", posx, posz,scrap_location, loc_barcode, name,
    # usage, "xml-id van de partner", "xml-id van de locatie",
    # "xml-id van de removal strategy", no_import
    with open("odoo_import_images.csv","w+") as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"')
        prod_ids = e('product.template','search',[])
        for prod_id in prod_ids:
            img_ids = e('product.template','read',prod_id).get('tmpl_extra_image',False)
            if img_ids:
                for img_id in img_ids:
                    img = e('mob.extra.image','read',img_id)
                    type_ids = img['image_type']
                    types = []
                    for type_id in type_ids:
                        types.append(e('mob.image.type','read',type_id)['name'])
                    if img['image']:
                        writer.writerow([prod_id, False, img['image'], img['mage_file'],
                            img['mage_product_id'], ','.join(types)])

if __name__ == "__main__":
    var_config = read_config()
    convert(var_config)
