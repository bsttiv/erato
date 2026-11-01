# Additional test proposals — 2026-10-30

These ideas are **unapproved and unimplemented**. No numeric case IDs are assigned.
The approved decision 06/09/14 area rules are implemented separately in backend tests.

| Area | Proposed behavior requiring the author's decision |
| --- | --- |
| REV | Restore lyrics after their historical chord IDs were deleted: reject, restore dependencies, or omit placements? Current implementation rejects invalid references without writes. |
| REV | Restore historical auto-key metadata when that key is no longer a candidate: reject or reset? Current implementation rejects the invalid explicit selection. |
| SLUG | Force a random slug collision during simultaneous publication and specify bounded retry behavior. |
| SONG / R2 | Force failure halfway through deleting several demo objects, or during MongoDB commit after R2 deletion; define recovery without inventing an unapproved outbox or persistence field. |
| SONG | Define a stable tie-break order when multiple songs have identical `updated_at`. Current order is descending date only. |
| INV | Define explicit pagination and maximum band-name length before implementing their boundary tests. Current lists are unpaginated; names are nonempty after trimming. |
| INV / PERM | Define whether song member lists should enumerate implicit band members as well as the owner and direct song members. Current lists show owner and direct memberships only. |
