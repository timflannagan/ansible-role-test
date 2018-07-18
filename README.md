Initial Testing Module
======

Runs an ansible playbook and verifies those results against available system information

To-Do:
======
1. Refactor the names of the verify_fs and verify_mount:
	- These functions verify the same things, but use different methods
2. Implement verify_disk_mount stub
3. Implement test_absent_status stub
	- This will need significant work 

Current Problems:
=====
- Figure out how to find free space in a volume group
- Figure out what other byte sizes are used in size variable, for verify_size method