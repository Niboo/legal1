Report to printer location
==========================

This module allows the configuration of printers based on report and location.

This can be used to e.g. select the nearest printer based on currently logged
in location for any given report. E.g. a stock picking will be printed on the
nearest A4 printer, while a shipping label will be printed on the nearest label
printer.

Users can be configured so that their work location is reset upon login. These
users are not allowed to print documents before reconfiguring their session's
work location (documents are printed to the UI instead).

This module also includes a method to print asynchronously in a new thread.
Note that this disables the authentication on the barcode generator API,
because the session is not available in the new thread.
