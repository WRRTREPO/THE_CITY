# Proof Kernel Implementation Evidence — v0.1.0

**Status:** Superseded — nonconformant reference candidate  
**Verified:** 2026-08-26  
**Specification:** [Three-Area Causal Proof Kernel — v0.1.0](Three-Area%20Causal%20Proof%20Kernel%20-%20Draft.md)  
**Implementation:** [kernel.py](proof_kernel/kernel.py)  
**Automated checks:** [test_kernel.py](proof_kernel/test_kernel.py)

**Superseded by:** [Proof Kernel Implementation Evidence — v0.1.1](Proof%20Kernel%20Implementation%20Evidence%20-%20v0.1.1.md), after conformance review found future-edge gating, mid-route cleanup, believed-input provenance, and failed-dispatch-state defects. The original test output below is retained as the historical candidate record.

## Scope

This evidence covers the dependency-free Python reference implementation of the frozen Ash Crossing proof kernel. It is a deterministic simulation proof, not an Unreal integration and not an authorization to expand city scope.

## Validation command

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY/proof_kernel"
PYTHONDONTWRITEBYTECODE=1 python3 test_kernel.py
```

Result: six of six checks passed.

1. Primary fire path closes the bridge, fails the police dispatch, and gives gang ownership at `74 / 26`.
2. Removing only the fire produces the counterfactual: police reaches `C`, gang completion fails, and ownership remains contested.
3. Police traversal occurs in canonical order before the faction completion at `t2`.
4. Route leases and faction personnel reservations are cleared or transformed at terminal states.
5. Two runs with the same record, seed, inputs, and simulation version produce identical canonical JSON and SHA-256 output.
6. The materialized scene facts do not contradict the authoritative bridge, police, or ownership state.

## Observed proof outputs

```text
primary_sha256=7f9f69fd8355690586c20708ce403d509fbce075223a34cbe2a089d4756762da
counterfactual_sha256=646cf923513b3fd48126933f0015565afb2e54fd87dc048668acbc54f9d12830
primary_owner=gang
counterfactual_owner=contested
```

## Reproducibility record

```text
runtime: Python 3.9.6
kernel.py sha256: 82cf425982c1bd1757b9a3c8f494c4cc4f19d3692a3544c5b5888394837fea8a
test_kernel.py sha256: ac437b3cc35976d2c79575a39ae74d29089816efb08d41091b7ccfbcca8ca5b6
bytecode artifacts generated: none
```

## Boundary

The frozen scenario remains unchanged. The proof establishes only its primary run, required counterfactual, deterministic replay, causal ledger, traversal and terminal cleanup, and materialization projection. Any additional city behavior requires a new scoped specification and acceptance record.
