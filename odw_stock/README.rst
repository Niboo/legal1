Small customizations in warehousing for Onderdelenwinkel
========================================================

* Set names of stock locations to untranslatable
* Force retrieval of related field 'Destination location' on the picking (referring to the location on its stock moves) without prefetching, so that the display of a picking list view is much faster. Prefetching is slow on a related field through a one2many field with many items (and there are some very large incoming pickings in this customer database). 
