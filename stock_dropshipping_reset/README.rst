Allow dropshipping orders to be reset to regular orders
=======================================================
Sales orders which are procured through dropshipping can sometimes still be
reset to regular procurement. This module provides a process for that, which
is accessible to the *purchase* manager through a button on the sales order
labeled *Rollback dropshipping*. This button is only visible on orders of which
every line is set to dropshipment.

Depending on the status of the procurements of each order line, this will allow
a reset of the procurement. Quantities on existing purchase orders will be
decreased, and the procurement route as well as the route on the sales order
line will be cleared, giving precedence to the routes that are configured on
the product.
