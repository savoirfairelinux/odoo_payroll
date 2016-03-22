================
Advanced Payroll
================

Advanced version of the Odoo Payroll by Savoir-faire Linux.

This set of module was designed for the Canada payroll. It allows
managing employee benefits, hourly rates, payroll periods, leave accruals,
importing worked days from timesheet and many other features.

This set of module is totally independant from the Odoo hr_payroll module.
payroll_base and payroll_account are forks of hr_payroll and hr_payroll_account
These are based on version 8.0 of Odoo and therefore remain under the AGPL v3.

The rest of modules are from Savoir-faire Linux with little contributions
from other people on OCA.

The reason for keeping Advanced Payroll independant from external modules, such as
from OCA or the Odoo source code is to preserve the coherence of the modules. Each module
within Advanced Payroll is compatible with each other. The python code will not change significantly from an Odoo release to another. For instance, the relational model should not change. This allows easier migrations from a release of Odoo to another, and reduces the cost of maintenance.
