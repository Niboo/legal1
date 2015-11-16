Delay sales procurements when using just-in-time
================================================
While we want to use just-in-time procurement for most of the system, for our
purposes the procurements of a sale order should only be processed in a manual,
controlled process, involving the procurement scheduler.

This module tweaks the JIT modules from Odoo core so that sale procurements
are not processsed automatically.

Technical note: if you introduce other modules that include new procure
methods, i.e. provide their own override of procurement.order::run(), then
that module needs to be added to this module's database to guarantee that the
JIT-no-sale mechanism has precedence over all the other procure methods.
