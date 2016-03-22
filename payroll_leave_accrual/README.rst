Leave Accrual
=============

This module adds leave accruals on employees and a mechanism to compute these
automaticaly.

The amounts for a leave type can be accruded
in cash, in hours or both.


Configuration
=============

 - Go to: Human Ressources -> Configuration -> Leaves Types
 - Select a leave type over which you wish to accrued amounts.
 - In the form view, go to the "Leave Accruals" tab.
 - Select payslip lines over which the leave type will be accruded.
 - If a salary rule gives a positive amount and you need to decrease the leave accrual from this amount,
   you need to set the field "Substract Amount" True.

The leave allocation system may be used to increase the hours accruded for a leave type.
For this, the field "Increase Accruals on Allocations" on the leave type must be True.
An example of use for this feature is for sick leaves.


Credits
=======

Contributors
------------

.. image:: http://sflx.ca/logo
   :alt: Savoir-faire Linux
   :target: http://sflx.ca

* David Dufresne <david.dufresne@savoirfairelinux.com>
* Maxime Chambreuil <maxime.chambreuil@savoirfairelinux.com>
* Pierre Lamarche <pierre.lamarche@savoirfairelinux.com>
