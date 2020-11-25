============
Horizon Bugs
============

Horizon project maintains all bugs in
`Launchpad horizon <https://bugs.launchpad.net/horizon>`__.

Bug Tags
--------

Tags are used to classify bugs in a meaningful way.
Popular tags are found at
`OpenStack Wiki <https://wiki.openstack.org/wiki/Bug_Tags>`__
(See ``Horizon`` and ``All projects`` sections).

Triaging Bugs
-------------

One of the important things in the bug management process is
to triage incoming bugs appropriately.
To keep you up-to-date to incoming bugs, see
`Receiving incoming bugs`_.

The bug triaging process would be:

* Check if a bug is filed for a correct project.
  Otherwise, change the project or mark it as "Invalid"
* Check if enough information like below is provided:

  * High level description
  * Step-by-step instruction to reproduce the bug
  * Expected output and actual output
  * Version(s) of related components (at least horizon version is required)

* Check if a similar bug was reported before.
  If found, mark it as duplicate (using "Mark as duplicate" button
  in the right-top menu).
* Add or update proper bug tags
* Verify if a bug can be reproduced.

  * If the bug cannot be reproduced, there would be some pre-conditions.
    It is recommended to request more information from the bug reporter.
    Setting the status to "Incomplete" usually makes sense in this case.

* Assign the importance.
  If it breaks horizon basic functionality, the importance should be
  marked as "Critical" or "High".

Receiving incoming bugs
-----------------------

To check incoming bugs, you can check Launchpad bug page directly,
but at the moment the easiest way is to subscribe Launchpad bug mails.
The steps to subscribe to the Launchpad bugs are as follows:

* Go to the `horizon bugs page <https://bugs.launchpad.net/horizon>`__.
* On the right hand side, click on "Subscribe to bug mail".
* In the pop-up that is displayed, keep the recipient as "Yourself",
  and set the subscription name to something useful like "horizon-bugs".
  You can choose either option for how much mail you get, but keep in mind that
  getting mail for all changes - while informative - will result in more emails.

You will now receive bug mails from Launchpad when a new bug is filed.
Note that you can classify emails based on the subscription name above.
