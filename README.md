Initial Testing Module
======

Runs an ansible playbook and verifies those results against available system information

To-Do:
======
1. Refactor the names of the verify_fs and verify_mount:
	- These functions verify the same things, but use different methods
2. Implement the verify_size_percentage function
    - This should be the last big thing to implement

Current Problems:
=====
- Figure out how to find free space in a volume group
- Figure out what other byte sizes are used in size variable, for verify_size method