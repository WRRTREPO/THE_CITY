# Proof Kernel Implementation Evidence — v0.1.1

**Status:** Passed — conformant reference candidate  
**Verified:** 2026-08-26  
**Specification:** [Three-Area Causal Proof Kernel — v0.1.0](Three-Area%20Causal%20Proof%20Kernel%20-%20Draft.md)  
**Supersedes:** [Proof Kernel Implementation Evidence — v0.1.0](Proof%20Kernel%20Implementation%20Evidence%20-%20v0.1.0.md)  
**Implementation:** [kernel.py](proof_kernel/kernel.py)  
**Automated checks:** [test_kernel.py](proof_kernel/test_kernel.py)

## Corrected conformance

This evidence records the four corrections required by the conformance review:

1. Police dispatch now tests only the current `E_AB` entry gate. `E_BC` is tested at `t1/20`, immediately before entry.
2. An `E_BC` closure before entry fails the traversal at `B`, releases all leases, records a terminal disposition, and returns the police unit to `available` at `B`.
3. Every ledger entry includes explicit `believed_inputs`; in this kernel they equal the actors' snapshot-observed inputs.
4. A failed primary dispatch now writes its result and failed gate into the authoritative police state as required by the frozen scenario.

## Validation command

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY/proof_kernel"
PYTHONDONTWRITEBYTECODE=1 python3 test_kernel.py
```

Result: eight of eight checks passed.

1. Primary fire path closes the bridge, fails dispatch, and gives gang ownership at `74 / 26`.
2. Removing only the fire brings police to `C`, fails gang completion, and leaves ownership contested.
3. Counterfactual traversal commits in canonical `E_AB → B → E_BC → C` order before faction completion.
4. Route leases and faction personnel reservations are cleared or transformed at terminal states.
5. A future `E_BC` state does not block police dispatch at `A`.
6. A closure before `E_BC` entry terminates traversal at `B`, releases police, and prevents arrival at `C`.
7. Replay with the same record, seed, inputs, and simulation version is byte-identical.
8. Every ledger entry has required observed and believed inputs plus mutation provenance; materialized facts do not contradict city truth.

## Observed proof outputs

```text
primary_sha256=d08e69d6b5fde3b27d10fb45f3bfd6143d856750c2dfd91f7b5851674fbeed76
counterfactual_sha256=0b27ed07131ab5889d820476ef7d665c1f5c046872ea895b93b764801e7c7206
mid_route_sha256=d16eb3d70b52ef8f8cb5acfb41572e8b9b5c04a9475c78774d487b79f3f03149
primary_owner=gang
counterfactual_owner=contested
mid_route_police_location=B
```

## Reproducibility record

```text
runtime: Python 3.9.6
kernel.py sha256: 3ae9b961d7302aa999e59c2dd87e26f0e6eb55f105f30decb3132a6d0f32e2c3
test_kernel.py sha256: 0cd6c1e903688a7b5a611ba3f4f44127d6e081585df13fea54463384f523d5be
bytecode artifacts generated: none
```

## Boundary

The frozen scenario remains unchanged. This proof establishes only its primary run, required no-fire counterfactual, traversal failure cleanup, deterministic replay, causal ledger, and materialization projection. It does not authorize map-scale or city-system expansion.
