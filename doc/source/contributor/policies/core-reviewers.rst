==================
Core Reviewer Team
==================

The horizon core reviewer team is responsible for many aspects of the
horizon project. These include, but are not limited to:

- Mentor community contributors in solution design, testing, and the
  review process
- Actively reviewing patch submissions, considering whether the patch:
  - is functional
  - fits use cases and vision of the project
  - is complete in terms of testing, documentation, and release notes
  - takes into consideration upgrade concerns from previous versions
- Assist in bug triage and delivery of bug fixes
- Curating the gate and triaging failures
- Maintaining accurate, complete, and relevant documentation
- Ensuring the level of testing is adequate and remains relevant as
  features are added
- Answering questions and participating in mailing list discussions
- Interfacing with other OpenStack teams
- Helping horizon plugin maintenances

In essence, core reviewers share the following common ideals:

- They share responsibility in the project's success in its mission.
- They value a healthy, vibrant, and active developer and user community.
- They have made a long-term, recurring time investment to improve the project.
- They spend their time doing what needs to be done to ensure the project's
  success, not necessarily what is the most interesting or fun.
- A core reviewer's responsibility doesn't end with merging code.

Core Reviewer Expectations
--------------------------

Members of the core reviewer team are expected to:

- Attend and participate in the weekly IRC meetings (if your timezone allows)
- Monitor and participate in-channel at #openstack-horizon
- Monitor and participate in ``[horizon]`` discussions on the mailing list
- Participate in related design sessions at Project Team Gatherings (PTGs)
- Review patch submissions actively and consistently

Please note in-person attendance at PTGs, mid-cycles, and other code sprints is
not a requirement to be a core reviewer. Participation can also include
contributing to the design documents discussed at the design sessions.

Active and consistent review of review activity, bug triage and other activity
will be performed periodically and fed back to the core reviewer team
so everyone knows how things are progressing.

Code Merge Responsibilities
---------------------------

While everyone is encouraged to review changes, members of the core
reviewer team have the ability to +2/-2 and +A changes to these
repositories. This is an extra level of responsibility not to be taken
lightly. Correctly merging code requires not only understanding the
code itself, but also how the code affects things like documentation,
testing, upgrade impacts and interactions with other projects. It also
means you pay attention to release milestones and understand if a
patch you are merging is marked for the release, especially critical
during the feature freeze.

Horizon Plugin Maintenance
--------------------------

GUI supports for most OpenStack projects are achieved via horizon plugins.
The horizon core reviewer team has responsibility to help horizon plugin teams
from the perspective of horizon related changes as the framework,
for example, Django version bump, testing improvements, plugin interface
changes in horizon and so on. A member of the team is expected to send and
review patches related to such changes.

Note that involvements in more works in horizon plugins are up to individuals
but it would be nice to be involved if you have time :)
