# Sources lane

Status: COMPLETE

No remote endpoint or neural signal was opened.  The only source object used
by the implementation is the predecessor's local canonical E1 metadata
receipt.  It supplies canonical session/specimen/split byte identities but
does not authenticate an Allen server response.

The neural observation, preprocessing, analysis contract, and model family
are represented by lowercase SHA-256 identities.  A digest proves equality
of bytes, not origin, correctness, coverage, or biological meaning.  Actual
remote and observation receipts remain external prerequisites.
