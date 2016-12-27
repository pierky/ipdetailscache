Release History
===============

0.4.8
-----

- Fix a packaging issue.

0.4.7
-----

- PeeringDB API is no longer in beta: URL updated.
  
0.4.6
-----

Fixes
_____

- Wrong behaviour when a cached IP address expires.

0.4.5
-----

Fixes
_____

- Behaviour change in IXPs info: if WhenUse != 0 check for IXPs info also for cached addresses having IsIXP == None

0.4.4
-----

Fixes
_____

- Force UTF-8 on IXPs info download

0.4.3
-----

Fixes
_____

- In case of missing or bad IXPs info from PeeringDB, raise IPDetailsCacheIXPInformationError

0.4.0 to 0.4.2
---------------

New Features
______________

- New packaged version
- PEP8
- .md to .rst for better PyPI readability

0.3.0
--------------

New Features
______________

- IXPs information
