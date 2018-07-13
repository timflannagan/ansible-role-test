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
