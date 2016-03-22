=================
Odoo Payroll Base
=================

This module is a fork from hr_payroll.
The module hr_payroll is problematic for many reasons, but first, a lack of unit test.
This module removes most odd features from hr_payroll and reimplements the models with the new api.

One thing this module removes is all the char fields manually entered by the end user.

Added features
==============
The objects available in the salary rules are now record sets.
The salary rule can reference itself with the variable 'rule'.
