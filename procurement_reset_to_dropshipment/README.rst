Reset procurement to dropshipment by magneto order no.
======================================================
When orders are reset to dropshipment in Magento, the order route in odoo needs
to be adapted accordingly. This module provides a wizard to do so in the Odoo
interface. To minimize the chance of the sale order procurement having already
been processed, we combine this process in the same wizard.

Magento pushes order csv files to a specific location for each order that has
been reset to dropshipment. Configure this path in the company settings, under
the *Settings* tab.
In the purchase menu, you can find an item *Run scheduler* available for the
purchase manager. This runs a two step wizard.

During the first step, the dropshipment files are retrieved and processed. Any
orders are logged in the interface as well as in the background server log and
in the sale order message thread. Upon a successful reset of the procurement
route, the CSV file will be attached in the sale order thread and then deleted
from the pick-up directory.

After a successful processing of the dropshipment files, the user can proceed
to run the procurement scheduler. Due to the dependency on
procurement_jit_no_sale, sale procurements will be held until this step is run.

Technical notes
---------------
This module introduces an active field on the procurement order. Sale order
procurements are set to inactive. Procurements older than a small time frame
are reactivated when the scheduler is run. This way we implement a grace time
to prevent a race conditions concerning orders that are being submitted after
the orders have been reviewed in Magento.
