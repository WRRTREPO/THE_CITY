# CITY ControlTower Entry

Work here: `/Users/boandersson/Projects/CITY`.
Origin remains `https://github.com/WRRTREPO/THE_CITY.git`.
The folder name changes. The game and Unreal module names do not.

Start with [the current CITY handover](handover.md). Phase 4 is sealed. Phase 5 specification is frozen in `PHASE_5_FREEZE.json`. `PHASE_5_SELECTION.json` records the operator-selected Live Cross-Domain Evidence Round-Trip Proof. The original handover remains byte-preserved in [the historical archive](References/Handover/handover-2026-08-30.md). The native preservation check verifies that archived original plus the other 652 original files in place.

The original checkout and its generated Unreal build files remain on Desktop. This clone has the committed source, hydrated LFS evidence, and complete original-history bundle. The two imported references retain their bytes.

`README.md` is part of the sealed release. Its historical Desktop commands remain unchanged. Use these commands from CITY:

| Command | Result |
| --- | --- |
| `./start.sh strategic-status --json` | Current sealed proof, capacity, authority, and selected successor freeze state. |
| `./start.sh health --json` | Original byte integrity, governance presence, references, and current receipt state. |
| `./start.sh next-action --json` | The frozen specification checker and governed implementation preparation. |
| `./start.sh rollback-plan --json` | Reviewable rollback steps. Executes no rollback. |
| `./start.sh validation-state --json` | Whether the stored verification receipt matches current HEAD, tree, and files. |
| `./start.sh verify-release --json` | Runs the frozen 172-member release verifier with isolated temporary output. |

The full declared native interface contains these six routes. Historical proof acquisition scripts remain discoverable in `proof_kernel/` and the original README. Their frozen contracts still apply. Native coverage counts the declared ControlTower interface; it does not mean every historical script is safe to run through a generic dispatcher.

From Projects, use `./ControlTower repo CITY capabilities --json` and `./ControlTower repo CITY run <action-id> --approve --json`. Every action has explicit argv, JSON assertions, timeouts, and source/runtime/evidence/external effects. Refresh the mount after committing.

The release verifier checks stored evidence. It does not launch or rebuild Unreal here. Historical dependency commitments point at the original Desktop project. A live CITY acquisition needs separate permitted validation. Health stays degraded while that boundary is unverified.

Onboarding evidence lives in Projects `Synthesis/CITYOnboarding/` and the owning mount, closure, and telemetry directories. This is local development evidence.

`claims.phase_5_authorized=false` means game implementation is not authorized by this interface. The separate `phase_5=specification_frozen` state records the operator-approved freeze of exact draft 3. The reviewed document and contract remain byte-identical. Native routes validate the pinned freeze, candidate commit/tree and preserved independent review. Remaining MCDP gates, the exact emitted PhoenixRising handoff and a clean implementation contract precede game implementation. Structural validation grants no game seal or live-runtime claim.
