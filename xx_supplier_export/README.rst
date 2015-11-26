Add purchase order CSV when emailing to suppliers
=================================================
Add a field to the partner form, *Purchase CSV template*. If defined, the field
value will be used as a template for a CSV file that is attached when sending
out purchase orders or RFQs for the supplier. The template is applied to each
order line.

The template should be formatted as a comma separated list of field references
or fixed values. The latter should be enclosed in double quotes. If the
template only consists of one value, please add a trailing comma.

In the template, the following objects can be referred to:

* *line*: the purchase order line that the template is applied to
* *order*: the purchase order that the line belongs to
* *seller*: the supplier information for the product of the line

Examples:
=========

Canonical example containing the supplier's product code, the product quantity
and the internal purchase order reference:

.. code::

    seller.product_code,line.product_qty,order.name

Example how to refer to literal values or use string substitution:

.. code::
   
    24085,"Onderdelenwinkel.nl","Product: %s" % line.product_id.name
