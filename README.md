Initial Testing Module
======

Runs an ansible playbook and verifies those results against available system information

To-Do:
======
1. Implement verify_present_status
2. 

Current Problems:
=====
1. x%PVS is programmed to calculate and verify x% of the total size of the specified PV (disks).
	- This isn't the case when there's isn't enough space in the PV to accommodate the specified percentage. It will shrink to the remaining space. 
2. %VG isn't idempotent, which could make verification difficult.
	- Usually the ansible-playbook will error though.
3. Think about what to check when device type is 'lvm' in is_invalid function