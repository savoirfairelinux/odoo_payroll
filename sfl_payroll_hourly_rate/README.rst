.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
Worked Days Hourly Rate
=======================
 * Adds hourly rate field on worked days
 * Adds date_from and date_to fields
 * Adds a rate (%) by which to multiplicate the hourly rate
 for overtime or other purposes.

How to use it
-------------
In the python script of a salary rule, you may call it via the payslip
browsable object:
    variable = payslip.get_rule_variable(rule_id, payslip.date_from)

rule_id always refer to the current rule.

If you need more than one variable for a salary rule, use a python dict.

Contributors
------------
* David Dufresne <david.dufresne@savoirfairelinux.com>
* Pierre Lamarche <pierre.lamarche@savoirfairelinux.com>
* Maxime Chambreuil <maxime.chambreuil@savoirfairelinux.com>
