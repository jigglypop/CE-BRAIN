# E1 metadata provenance: canonicalization and split audit

Status: COMPLETE

Scope: this lane audits only the deterministic metadata apparatus in
`00-contract.md`.  It performs no AllenSDK, network, NWB, unit, channel,
probe, LFP, spike, covariance, dimension, or model-score operation.  It makes
no biological claim.

## Concrete findings first

1. **The revised contract resolves the inherited action conflict.**  It pins
   the release/source identity and makes the public warehouse session query,
   rather than `get_session_table(suppress=[])`, the only admissible remote
   method.  This lane accepts that as an input provenance constraint; it does
   not independently assert the source fact.
2. **The split formula is mathematically unambiguous only after a strict
   identifier encoding is fixed.**  `g` must be the ASCII base-10 rendering
   of a nonnegative, non-Boolean integral `specimen_id`, with no sign,
   whitespace, decimal point, exponent, or leading zeros except `0`.  Hashing
   `"03"`, a float `3.0`, a NumPy-formatted value, or a locale string instead
   of `"3"` changes the group and is an apparatus error.
3. **The revised contract closes the core P1 canonicalization gap.**  It now
   fixes ID encoding, timestamp grammar and precision, NFC strings,
   byte-identical duplicate handling, separate assignment JSONL, and the
   exact two-run byte streams.  Optional fields remain excluded unless a
   later source contract gives them an audited schema.
4. **The specimen split itself prevents cross-split specimen leakage.**  It
   does not guarantee an adequate eventual *eligible* sample: the required
   two-specimen minimum can be evaluated only after a separately locked
   eligibility definition exists.  No rehashing or movement is permitted if
   that later gate fails.

## Definitions and exact arithmetic

Let `ASCII10(g)` be the canonical base-10 bytes of an allowed `specimen_id`.
For the frozen byte salt $S=\texttt{CE-E1-NEUROPIXELS-V1}$, define

$$
D_g=\operatorname{SHA256}(S\mathbin\Vert\texttt{:}\mathbin\Vert
\operatorname{ASCII10}(g)),\qquad
H_g=\sum_{j=0}^{7}D_g[j]2^{8(7-j)}\in\{0,\ldots,2^{64}-1\}.
$$

No floating-point operation is needed.  The allocation is exactly

$$
A(g)=\begin{cases}
\mathrm{calibration},&H_g<2^{63},\\
\mathrm{development},&2^{63}\le H_g<3\,2^{62},\\
\mathrm{held\_out},&3\,2^{62}\le H_g<2^{64}.
\end{cases}
$$

This is equivalent to the contract's $u(g)=H_g/2^{64}$ cutpoints but
avoids boundary and binary-float ambiguity.  The intervals are disjoint and
their integer union is $[0,2^{64})$, hence every valid specimen has exactly
one allocation.  Big-endian is essential: changing it changes $H_g$ and
therefore can move subjects between splits.

Independent test vectors (full digest prefix is intentionally fixed by the
fixture) are:

| `specimen_id` | `H_g` | allocation |
|---:|---:|---|
| 0 | 7371522747307704441 | calibration |
| 2 | 17843654490131864117 | held_out |
| 3 | 12960670049301555441 | development |

The fixture verifies these values with SHA-256 and `int.from_bytes(...,
"big", signed=False)`, not a decimal approximation.

## Canonical row and byte rules required for implementation

Materialize the official index as `ecephys_session_id` *before* validation.
For each required core field, use the following closed schema:

| Field | admitted value | canonical value | failure |
|---|---|---|---|
| `ecephys_session_id`, `specimen_id` | dependency-free core: built-in `int` only, nonnegative and not Boolean | ASCII base-10 JSON string | `E1_FIELD_TYPE_INVALID` |
| `session_type` | nonempty Unicode string; NFC-normalize, then reject any Unicode `Cc` control character | NFC UTF-8 JSON string | `E1_FIELD_TYPE_INVALID` |
| `date_of_acquisition` | strict offset-aware RFC3339 subset `YYYY-MM-DDTHH:MM:SS(.1...6 digits)?(Z or +/-HH:MM)`; no naive date/time and no named/unknown zone | UTC `YYYY-MM-DDTHH:MM:SS.ffffffZ` | `E1_TIMEZONE_UNRESOLVED` or `E1_FIELD_TYPE_INVALID` |

Reject non-finite numbers everywhere.  Optional fields must each have a
pinned admissible type and normalization rule; an optional list is an ordered
data value unless the source contract explicitly declares it set-valued.  If
it is set-valued, normalize every scalar then sort by normalized Unicode code
point order and reject duplicates.  Never silently coerce unsupported values.

The dependency-free core deliberately accepts only built-in `int`: it does not
silently rely on NumPy or pandas scalar semantics.  A future pandas/NumPy
adapter must first establish that its scalar is exactly integral and
nonnegative, reject Boolean/float/NaN/Infinity/string forms, then pass the
resulting built-in `int` to this core.  It must not widen the hash domain.

For the core table, form an object with exactly the four canonical keys, emit
JSON with lexicographically sorted keys, compact `,`/`:` separators,
`ensure_ascii=false`, UTF-8, and LF (`0x0a`) after every row.  Sort rows by
integer session ID.  Do not include run timestamp, locale, host path, package
location, or other variable execution metadata in the table bytes.

For a repeated session ID, byte-identical canonical core-plus-retained-
optional rows may be deterministically deduplicated and recorded in a
diagnostic count; any nonidentical repetition is
`E1_INCONSISTENT_DUPLICATE_SESSION`.  In either case, a session cannot map to
multiple specimens.  The implementation must select one of two policies for
exact duplicates in its source contract: **reject all duplicates** or
**deduplicate byte-identical rows**.  The synthetic fixture covers the latter;
mixing policies across runs is invalid.

In addition to the session-table JSONL, emit a separately hashed assignment
JSONL, one row per canonical session with exactly
`ecephys_session_id`, `specimen_id`, and `split`, sorted by session integer.
This resolves the phrase "every session/specimen split assignment" into
reproducible bytes.  A receipt's non-deterministic acquisition timestamp must
be outside both byte hashes.  Thus "two-run byte determinism" means equality
of the table and assignment byte streams and their SHA-256 values for the same
pinned response bytes, not equality of an entire receipt that records two
different invocation times.

## Proof of allocation isolation and its limit

For any two canonical rows whose specimen IDs equal $g$, the input bytes to
SHA-256 are identical, so determinism of SHA-256 gives the same $D_g$,
$H_g$, and $A(g)$.  Therefore all sessions of a specimen enter one and
only one split.  Consequently, eligibility rules applied afterward within
each allocated subset cannot create cross-split specimen overlap.

This proof assumes the source's `specimen_id` correctly represents the
independent grouping unit.  It neither establishes biological independence
nor prevents a source-level alias from assigning two physical specimens the
same identifier.  Required schema diagnostics and provenance pinning address
only the former representation problem.  It also cannot prove that each
future eligible partition has at least two specimens: filtering can remove
them.  The future locked eligibility step must count distinct specimen IDs in
each allocation and return `E1_SPLIT_APPARATUS_INVALID` before any endpoint
or score if any count is below two.

## Adversarial reproduction

Run:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-e1-metadata-provenance-lock-20260825\artifacts\math_metadata_split_fixtures.py
```

Result: `PASS: E1 metadata canonicalization and specimen-split adversarial fixtures`.
The pure-Python fixture has no import or call path to AllenSDK and tests:
big-endian vectors; same-input two-run table *and assignment* bytes plus both
SHA-256 values; integer session ordering; key-order invariance; NFC
normalization; control-character rejection; strict RFC3339 offset conversion
and naive/space-separated/over-precision timestamp rejection;
Boolean/float/negative ID rejection; missing and empty fields; exact duplicate
handling; and conflicting same-session rows.

## Findings classification

- **P0:** none found in the split arithmetic or fixture.
- **P1:** resolved for the four-field core by contract revision: schema,
  duplicate policy, assignment artifact, and deterministic-subset definition
  are frozen.  An implementation that retains optional fields without a
  separately audited optional schema would reopen P1.
- **P2:** the optional-field set-versus-list rule applies only if a later
  source contract elects to retain optional fields.
