Initial Testing Module
======

Runs an ansible playbook and verifies those results against available system information

To-Do:
======
1. Parse the test.yml file in tests directory
	- This is going to be problematic, and unnecessarily complicated
2. Finish creating all verification tests
	- Check blkid/lsblk info against /etc/fstab file
3. Look into adding unit testing using pytest

Current Problems:
=====
1. Is the organization of the playbook going to stay the same?
	- For instance, what's the last variable?
		* Could populate a dictionary that handles that by declaring defaults
2. Is this testing an entire test.yml file or pausing after each include_role test?
3. Parsing the test.yml file would be difficult
	- Could have a series of functions that verifies lsblk, /etc/fstab, blkid
		info against a test's expected results
			* Could pass a series of variables, then a dictionary of expected results 
