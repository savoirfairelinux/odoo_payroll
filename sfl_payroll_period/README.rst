.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============
Payroll Period
==============

Add the concept of payroll period.

The objective is not to restrict or complicate the payroll workflow.
It is meant to reduce the number of clicks related to date selections and avoid mistakes.

Add the date of payment on the payslip and payslip batch. This date is automatically filled when selecting
a period.

Add the company field on the payslip batch.
Add a sequence on the payslip batch name.


Configuration
=============

Create a fiscal year
--------------------
Go to: Human Resources -> Configuration -> Payroll -> Payroll Fiscal Year

 - Select a type of schedule, e.g. monthly
 - Select a duration, e.g. from 2015-01-01 to 2015-12-31
 - Select when the payment is done, e.g. the second day of the next period
 - Click on create periods, then confirm

The first period of the year is now open and ready to be used.

Some companies have employees paid at different types of schedule.
In that case, you need to create as many fiscal years as types of schedule required.
The same applies in a multi-company configuration.


Usage
=====

Create a payslip batch
----------------------
Go to: Human Resources -> Payroll -> Payslip Batches

The first period of the fiscal year is already selected.
You may change it if you manage multiple types of schedules.

 - Click on Generate Payslips

The employees paid with the selected schedule are automatically selected.

 - Click on Generate

 - Confirm your payslips

 - Click on Close

The payroll period is closed automatically and the next one is open.


Credits
=======

Contributors
------------
* David Dufresne <david.dufresne@savoirfairelinux.com>
* Maxime Chambreuil <maxime.chambreuil@savoirfairelinux.com>
* Pierre Lamarche <pierre.lamarche@savoirfairelinux.com>
* Salton Massally <smassally@idtlabs.sl>
