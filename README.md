Initial Testing Module
======

Runs an ansible playbook and verifies those results against available system information

To-Do:
======
2. Finish the percentage size verification functions for last.

Current Problems:
=====
1. x%PVS is programmed to calculate and verify x% of the total size of the specified PV (disks).
	- This isn't the case when there's isn't enough space in the PV to accommodate the specified percentage. It will shrink to the remaining space. 
2. %VG isn't idempotent, which could make verification difficult.
	- Usually the ansible-playbook will error though.

Notes/Issues:
=====
1. When calling any of the %[SIZE] options for the size variable, and there's an existing LV, it will resize that LV if there's free space. For the VG "foo", there were two LV's: test1, and test2. When calling the current playbook with the variable's roles, it kept one of the LV's the same, but changed the other from 7G to 10G (50% of the VG.)