.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Salary Rule Variables
=====================

Salary rule variables are amounts or python expressions that change over
the years. This module allows to compute these variables and reference
them from salary rules.

The purpose of this module is to be able to adapt a complexe salary structures
(e.g. the canadian income tax structure) from one year to another without
going each time through the whole testing procedure.

Numbers change but the whole logic stays the same.

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
