# External Input Boundary Proof Evidence

**Version:** 0.1.1
**Status:** Passed and sealed.
**Specification:** [External Input Boundary Proof — v0.1.1](External%20Input%20Boundary%20Proof%20-%20v0.1.1.md)
**Simulation identity:** `0.7.0-draft.45`
**Scope:** Canonical-only. No Unreal, transport, wall-clock, city-content,
randomness, same-time arbitration, late input, or production streaming claim.

## Verdict

> **A valid player-originated evidence input can interrupt an interval that a
> boundary-jump policy would otherwise skip, become its own canonical boundary,
> and change only the later autonomous work that ordinarily reads its result.**

The proof establishes this without making input, cursor, policy, or local
representation strategic authority.

```text
R0 @ t0/00
  autonomous next = alpha @ t1/00

Q available @ t0/30
  ↓ side-effect-free admission
BQ bound to hash(R0)
  ↓ canonical resolver
Rinput @ t0/30
  gate_token_state = disabled
  ↓ rediscover from Rinput
alpha @ t1/00
  ↓ ordinary gate revalidation
Rfinal
  alpha = failed_gate
```

## Execution results

The full Python regression record passed **130/130** checks. The new proof
suite passed **13/13** focused checks.

Four materially different local execution histories produced byte-identical
canonical checkpoints at `R0`, `Rinput`, and `Rfinal`:

```text
A  dense inspection throughout
B  boundary jump throughout
C  dense → demote → boundary jump
D  boundary jump → promote → dense
```

Only resolution-local samples, cache, and diagnostic traces differ.

The required coordinator/scheduler distinction was observed at every
checkpoint:

```text
R0
  next_consequential_boundary = alpha @ t1/00
  next_execution_boundary     = BQ @ t0/30

Rinput
  next_consequential_boundary = alpha @ t1/00
  next_execution_boundary     = alpha @ t1/00

Rfinal
  next_consequential_boundary = none
  next_execution_boundary     = none
```

The autonomous scheduler does not know about Q. The input-aware coordinator
admits Q separately, then the ordinary canonical scheduler is rediscovered
from the successor record.

## External successor-hash witness

No canonical record or in-record ledger stores a successor/post-state hash.
Each complete successor identity is computed and checked externally:

```text
H0  = bfa474a4cd761358abeef0351f8a84062a7386667446ec79bbbd5e3eed7c94ce
HI  = 608a5da29e28d28d850f04790922fdf146ed3bc05471d33c398d191db7300623
HF  = 06d0b6d59fdaf4fc01c96317e09589dca65e2d263b76d53a2dd72f4cbe48822b
HC  = e6c645f8d70f3439b3bda6079be3a09251c3d417b99246d2d40649bf27429212
```

The chain is inspectable without a self-hash:

```text
R0      → LQ.canonical_pre_state_hash = H0 → Rinput → HI
Rinput  → LAlphaFailed.canonical_pre_state_hash = HI → Rfinal → HF
R0 / no Q → LAlphaSucceeded.canonical_pre_state_hash = H0
          → Rcontrol_final → HC
```

Each successor also carries the exact predecessor as its singular canonical
ancestry parent.

## Causal witness

Q changes only the declared current gate-token facts. It does not cancel,
terminalize, reschedule, or otherwise command `commitment_alpha`.

At `t1/00`, alpha independently reads from `Rinput`:

```yaml
path: /current_causal_state/gate_relevant_state/gate_token_state
observed_value: disabled
required_value: enabled
result: false
```

Alpha therefore terminates as `failed_gate` and releases its reserved unit.

The Q-absent control starts with the same byte-identical `R0` and the same
alpha definition. It reaches `t1/00`, reads `enabled`, succeeds, and releases
the same reservation through its successful disposition.

## Authority and rejection witnesses

Side-effect-free admission rejects malformed Q before a canonical transaction,
cursor advance, or ledger append. The sealed rejection set covers:

- source-hash mismatch;
- digest-covered tampering without recomputation;
- redirected input with recomputed valid digest but invalid contract;
- late/equal-time input;
- attempted autonomous crossing of an earlier available Q;
- stale BQ against `Rinput`;
- cursor attempt to skip unaccepted Q;
- cached authoritative gate result or local canonical-mutation request;
- promotion carrying authority; and
- demotion losing authority.

Every rejected witness leaves its canonical input unchanged and is terminal in
this proof. Resetting the replay-local cursor after `Rinput` cannot reacquire
Q because canonical `accepted_external_inputs` already contains its identity.

The source audit records one side-effect-free admission path, one coordinator,
one autonomous scheduler, and one resolver for both BQ and alpha. It confirms
that no policy/local cache/trace evaluates an authoritative gate for resolver
use or calls the resolver; no random, Unreal, city-content, post-state-hash,
or input-result shortcut exists on the demonstrated path.

## Release package

`External Input Boundary Proof - v0.1.1 SHA256SUMS.txt` contains **25**
members and excludes itself. The verifier regenerates all artifacts from the
frozen resolver and evidence input, compares their exact canonical JSON, then
checks every release digest.

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_external_input_boundary_release.py verify
```

## Boundary

This proves one neutral external-input interval. It does not prove live input
transport, input ordering at the same time, late evidence, multiple streams,
multiple commitments, randomness, actual FPS fidelity transitions, networking,
rollback, save/load, map scale, or production streaming.
