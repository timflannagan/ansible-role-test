Initial Testing Module
======

Runs an ansible playbook and verifies those results against available system information

To-Do:
======
1. Refactor the names of the verify_fs and verify_mount:
	- These functions verify the same things, but use different methods.
2. Implement the verify_size_percentage function.
    - This should be the last big thing to implement.
3. Refactor the return value on most of these functions.
4. Clean up redundant functions.
5. Don't need to worry about %FREE except in the default 100%FREE specification.
6. Test the %VG function with MB data instead of GB.
	- This needs to be refactored some point soon.
7. Modify the parameters being passes to most functions.
	- Some of the helper functions are being passed data they don't need to touch.
8. Modify verify_vg_size_percentage to return failed (flag), used_space, free_space, total_space.
	- The helper function for verify_pv_size_percentage could use this too.
	- Assuming that this isn't the greatest idea.
9. verify_vg_size_percentage is very messy atm.
10. Re-implement verify_disk_mount

Current Problems:
=====
1. x%PVS is programmed to calculate and verify x% of the total size of the specified PV (disks).
	- This isn't the case when there's isn't enough space in the PV to accommodate the specified percentage. It will shrink to the remaining space. 
2. %VG isn't idempotent, which could make verification difficult.
	- Usually the ansible-playbook will error though.