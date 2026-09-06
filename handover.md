# CITY Session Handover

**Updated:** 2026-09-06
**Active repository:** `/Users/boandersson/Projects/CITY`
**Origin:** `https://github.com/WRRTREPO/THE_CITY.git`
**Authority:** Current session guidance. This file grants no implementation scope, capacity, or proof seal.

## Current state

**Phase 4 is sealed. Phase 5 is open for specification review only.**

The operator selected **Live Cross-Domain Evidence Round-Trip Proof** with “Approved. Execute”. The [selection record](PHASE_5_SELECTION.json) binds the [candidate specification](Live%20Cross-Domain%20Evidence%20Round-Trip%20Proof%20-%20Draft.md) and its machine-readable contract. This updates current development routing. It changes no historical seal. The candidate is unfrozen; independent review is pending.

| Record | Current value |
| --- | --- |
| Latest sealed proof | Cross-Domain Canonical Occupancy Materialization Proof v0.1.0 |
| Governing continuation | 0.7.0-draft.83 |
| Capacity record | THE_CITY Development Capacity and Progress Note v0.1.11 |
| Current working unit | Live Cross-Domain Evidence Round-Trip Proof specification review |
| Proof artifacts | 82 |
| Sealed release members | 172, excluding the manifest |
| Next development decision | Independent exact-candidate specification review, corrections, then freeze |

The sealed proof represents the exact canonical `R0 → Rtransit → Rfinal` occupancy chain across two original, simultaneously live Unreal domains. Canonical Python records own occupancy and completion. Unreal represents those records.

The recorded release checks passed: 45 focused tests, 215 predecessor regressions, and 34 rejected verifier adversaries. These are the bounded sealed proof results. They do not establish a production city, physical movement, multiplayer, or a new live run from CITY.

Phase 3 and Phase 4 are completed historical work. Do not resume their old candidate-review or implementation steps as the current task.

## Start here

Work from CITY. The Desktop checkout is preserved reference material.

```sh
cd /Users/boandersson/Projects/CITY
git status --porcelain=v2 --branch
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git rev-list --left-right --count HEAD...origin/main
./start.sh strategic-status --json
./start.sh health --json
```

The ahead/behind command compares the locally cached tracking ref. It does not fetch remote state. Use the live Git identity and receipt state; a historical handover commit is not the current checkout identity.

Read these current entry documents:

1. [Agent authority](AGENTS.md)
2. [ControlTower commands and boundaries](CONTROLTOWER_ONBOARDING.md)
3. [Runtime manifest](RUNTIME_MANIFEST.md)
4. [Current proof state and repo-agent instruction](THE_CITY%20Current%20Proof%20State%20and%20Repo-Agent%20Instruction%20-%20v0.1.0.md)
5. [Working continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
6. [Sealed Phase-4 evidence](Cross-Domain%20Canonical%20Occupancy%20Materialization%20Proof%20Evidence%20-%20v0.1.0.md)
7. [Capacity v0.1.11](THE_CITY%20Development%20Capacity%20and%20Progress%20Note%20-%20v0.1.11.md)

## Native verification

The installed ControlTower interface has six routes:

| Command | Result |
| --- | --- |
| `./start.sh strategic-status --json` | Current proof, capacity, and authority. |
| `./start.sh health --json` | Original-file preservation, governance, and receipt state. |
| `./start.sh next-action --json` | Next permitted verification command. |
| `./start.sh rollback-plan --json` | Rollback plan. Executes no rollback. |
| `./start.sh validation-state --json` | Whether the existing release receipt matches current files and HEAD. |
| `./start.sh verify-release --json` | Stored 172-member release verification. No Unreal launch. |

To run that verifier through ControlTower and persist an exact-HEAD receipt, use this from CITY:

```sh
../ControlTower repo CITY run city.verify-release --approve --json
```

ControlTower writes its local development receipts under `.controltower/receipts/`. Refresh the CITY mount after committing. A changed commit or file fingerprint makes the old validation receipt stale.

The repo-owned interface, adapter, profile, truth context, and managed SwedeVO mirror are installed. Mutation work still follows the local authority rules, sealed contract, active MCDP intake, and fresh Control Plane Gate. The operator has now selected the successor. Selection does not complete MCDP or create a PhoenixRising handoff. The active successor session is `mcdp-city-live-evidence-spec`.

## Original Git history after LFS conversion

Historical review and seal decisions refer to these original objects:

| Record | Original commit | Original tree |
| --- | --- | --- |
| Accepted Phase-4 candidate | `bee3ecca660f884f3af727affae3ab1ceae2c401` | `3302b4e34b412629776433a4b50b1b0a852e51ab` |
| Phase-4 forward seal | `5d4eac983de281fcf7b03d78453e5f131204b946` | `e01411b0af3e819474d33e73432148585ec6a34c` |

The approved LFS conversion changed six later Git identities. Do not substitute converted commit IDs for the original review or seal decisions. Their original objects are preserved in `References/Git History/THE_CITY-pre-LFS.bundle`; they are not available directly in this clone's current Git object database.

Verify and inspect the original history from CITY:

```sh
git bundle verify "References/Git History/THE_CITY-pre-LFS.bundle"
shasum -a 256 "References/Git History/THE_CITY-pre-LFS.bundle"
city_history_review="$(mktemp -d /private/tmp/city-original-history.XXXXXX)"
git clone --bare "References/Git History/THE_CITY-pre-LFS.bundle" "$city_history_review/repo.git"
git --git-dir="$city_history_review/repo.git" rev-parse 'bee3ecca660f884f3af727affae3ab1ceae2c401^{tree}'
git --git-dir="$city_history_review/repo.git" rev-parse '5d4eac983de281fcf7b03d78453e5f131204b946^{tree}'
```

Expected bundle SHA-256: `5dc6076cdcfeb880872e15adaca880b0f20255e28d1312b1597faac666ea1f0e`.

The two tree results must match the table above. For a full historical checkout and exact-release audit, follow [Git history and LFS transport](References/Git%20History/README.md). A plain archive of the converted branch contains an LFS pointer for the converted evidence file. Verify current releases on a hydrated checkout. Verify original sealed commits from the preserved history.

## Preserved handover history

The [2026-08-30 handover](References/Handover/handover-2026-08-30.md) retains all 1,135 original lines without byte changes. It records old review rounds, Desktop commands, and historical push observations. Its old “Read this first,” decision table, and return card are historical instructions. Use this CITY handover for the current session.

Original handover SHA-256: `c8ffd187ab0a5acccb55aad05a73bbe216c78f2c88ea384a9216ff748036e517`.

The original handover is outside the 172-member release. CITY's preservation check now verifies it at the archive path. The other 652 original files retain their original paths and hashes. The original baseline, sealed sources, manifests, and evidence remain unchanged.

## Remaining boundary

Live Unreal execution from `/Users/boandersson/Projects/CITY` remains unverified. The source project and module names remain `CityMaterializationProof`. Historical executable paths in sealed evidence remain provenance; this move does not rewrite them or prove a fresh Unreal build.

There is no open Phase-3 or Phase-4 implementation unit. Phase 5 is open for specification review only. Game implementation follows exact review and freeze. Do not regenerate sealed releases or launch historical acquisition commands to validate this document change.

Run the review-only checker from CITY:

```sh
python3 -B proof_kernel/validate_live_cross_domain_evidence_round_trip_spec.py --json
python3 -B proof_kernel/validate_live_cross_domain_evidence_round_trip_spec.py --self-test --json
```

The checker verifies structural commitments. It proves no Unreal execution or independent review acceptance.
