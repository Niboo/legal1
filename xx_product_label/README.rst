Product Labels Customization
============================
Provides a custom product label. Amongst other changes, the label features
the destination determined in the barcode scanning interface. The destination
refers to a specific procurement group (c.q. sales order number) or the
product's default putaway location.

Automatic prints of label and picking
=====================================
When scanning incoming products in the barcode scanning interface, a product
label is printed automatically for each scanned product. When it is detected
that a product is the first product to satisfy a linked (MTO) outgoing
picking, the picking slip is printed automatically as well.

Prints are sent to the printer in the background using the
base_report_to_printer module.

Integration with dyn_report_to_printer_location
===============================================
If a user does not have a work location configured for his session, and he or
she is configured to need one (as per the 'Reset work location on login'
checkbox, the user is not allowed to open the barcode interface before\
configuring a work location.

Print labels from the putaway location view
===========================================
From the product's putaway location's view there is a button that allows the
user to print the product label. The putaway location will be featured in the
bottom right corner on the label.

Integration with dyn_report_to_printer_location
===============================================
If a user does not have a work location configured for his session, and he or
she is configured to need one (as per the 'Reset work location on login'
checkbox, the user is not allowed to open the barcode interface before\
configuring a work location.
