#!/usr/bin/env python3
"""Generate and independently verify the frozen Phase-4 release boundary."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from cross_domain_canonical_occupancy_materialization import (
    ARTIFACT_NAMES,
    DOMAIN_ROLES,
    GUARD_STATES,
    HEAD_HASHES,
    HEAD_OBSERVATION_SCHEMA,
    LIVE_OBSERVATION_SCHEMA,
    MATERIALIZATION_RECEIPT_SCHEMA,
    MATERIALIZATION_STAGES,
    OPERATION_ROWS,
    PRIMARY_REFRESH_ORDERS,
    PROCESS_BINDING_FIELDS,
    PROOF_SCENARIO,
    PROOF_VERSION,
    PROJECTION_ROWS,
    RAW_HASHES,
    RECORD_FILENAMES,
    RECORD_ROLES,
    RECORDS,
    ROOT,
    artifact_role_set_valid,
    bind_invocation,
    canonical_chain,
    canonical_json,
    compare_expectation_receipt_observation,
    expected_representation,
    guard_and_head_observation_matrix,
    is_sha256,
    operation_invocation,
    operation_tuple_matrix,
    operational_process_instance_id,
    process_binding,
    process_binding_raw_sha256,
    projection,
    projection_matrix,
    semantic_replay_projection,
    sha256_bytes,
    sha256_value,
    stored_json_bytes,
    strict_load_stored_json,
    validate_head_disposition,
    validate_materialization_receipt,
    write_json,
)
from cross_domain_canonical_occupancy_materialization_harness import (
    AUTHORITY_ROWS,
    HEAD_PUBLICATION_STAGES,
    LIVENESS_ROWS,
    MATERIALIZATION_CONTEXTS,
    OBSERVATION_CONTEXTS,
    OBSERVATION_STAGES,
    SOURCE_AUDIT_PATHS,
    SOURCE_CHECK_IDS,
    SOURCE_MUTATIONS,
    acquire_source_audit,
)


ARTIFACT_DIRECTORY = "proof_kernel/CrossDomainCanonicalOccupancyMaterializationProofRecords"
MANIFEST = "Cross-Domain Canonical Occupancy Materialization Proof - v0.1.0 SHA256SUMS.txt"
EVIDENCE_DOCUMENT = "Cross-Domain Canonical Occupancy Materialization Proof Evidence - v0.1.0.md"

NON_ARTIFACT_MEMBERS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md",
    "Canonical Spatial Topology Identity Proof - Draft.md",
    "Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md",
    "Canonical Spatial Topology Identity Proof - v0.1.0 SHA256SUMS.txt",
    "Canonical Occupancy Transition Proof - Draft.md",
    "Canonical Occupancy Transition Proof Evidence - v0.1.0.md",
    "Canonical Occupancy Transition Proof - v0.1.0 SHA256SUMS.txt",
    "Simultaneous Physical Domains Proof - Draft.md",
    "Simultaneous Physical Domains Proof - v0.1.1.md",
    "Simultaneous Physical Domains Proof Evidence - v0.1.1.md",
    "Simultaneous Physical Domains Proof - v0.1.1 SHA256SUMS.txt",
    "Cross-Domain Canonical Occupancy Materialization Proof - Draft.md",
    EVIDENCE_DOCUMENT,
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.11.md",
    "THE_CITY Developer Snapshot - v0.1.0.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_R0.json",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_start_boundary_H0.json",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_Rtransit.json",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_completion_boundary_Htransit.json",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_Rfinal.json",
    "proof_kernel/kernel.py",
    "proof_kernel/canonical_spatial_topology_identity.py",
    "proof_kernel/canonical_occupancy_transition.py",
    "proof_kernel/simultaneous_physical_domains.py",
    "proof_kernel/simultaneous_physical_domains_harness.py",
    "proof_kernel/test_canonical_occupancy_transition.py",
    "proof_kernel/test_simultaneous_physical_domains.py",
    "proof_kernel/verify_canonical_occupancy_transition_release.py",
    "proof_kernel/verify_simultaneous_physical_domains_release.py",
    "proof_kernel/cross_domain_canonical_occupancy_materialization.py",
    "proof_kernel/cross_domain_canonical_occupancy_materialization_harness.py",
    "proof_kernel/test_cross_domain_canonical_occupancy_materialization.py",
    "proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py",
    "CityMaterializationProof/CityMaterializationProof.uproject",
    "CityMaterializationProof/Config/DefaultEngine.ini",
    "CityMaterializationProof/Config/DefaultGame.ini",
    "CityMaterializationProof/Config/DefaultInput.ini",
    "CityMaterializationProof/README.md",
    "CityMaterializationProof/Source/CityMaterializationProof.Target.cs",
    "CityMaterializationProof/Source/CityMaterializationProofEditor.Target.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h",
)

CHANGED_NON_ARTIFACT_MEMBERS = frozenset({
    "README.md",
    EVIDENCE_DOCUMENT,
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Developer Snapshot - v0.1.0.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
    "proof_kernel/cross_domain_canonical_occupancy_materialization.py",
    "proof_kernel/cross_domain_canonical_occupancy_materialization_harness.py",
    "proof_kernel/test_cross_domain_canonical_occupancy_materialization.py",
    "proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h",
})

# These are the accepted-freeze bytes at 81b1cc9.  Hard-coding them keeps the
# 70-member unchanged boundary enforceable even in an isolated source export
# where Git history is deliberately unavailable.
UNCHANGED_NON_ARTIFACT_SHA256 = {
    "Canonical Occupancy Transition Proof - Draft.md": "4d1b2d88f758040706c8981d878b1e9b143d276d304fba34e9c0d096a516f91f",
    "Canonical Occupancy Transition Proof - v0.1.0 SHA256SUMS.txt": "06dc3e58be490f48365778a5e74924f52ca3e89e860044c48ad704c8ad730450",
    "Canonical Occupancy Transition Proof Evidence - v0.1.0.md": "ec0006d8107061c2a42c43d69e7c6f650a7878364bbac0432476036107706a44",
    "Canonical Spatial Topology Identity Proof - Draft.md": "b915152ec1402f21e654685a3f1de22b4b3228f15413f2731fa02378c1b9ba8a",
    "Canonical Spatial Topology Identity Proof - v0.1.0 SHA256SUMS.txt": "8b4eb45202b6db328cb53f5689e24d1b98bdce8331e1b2d9a960be09215c686c",
    "Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md": "7d59114d692a5bea4cdf6389d3b123d28c7dd9cd6aea756db044067aee1539a7",
    "CityMaterializationProof/CityMaterializationProof.uproject": "d4cf6ee332faf8705cd3eab6a3a9a2a110e5a41daa1c361e95a0181012aea7ac",
    "CityMaterializationProof/Config/DefaultEngine.ini": "68c6a6c0dd9362574b2b5ecb36e3b63dedc8cc53c5a962382c56736d10121aa7",
    "CityMaterializationProof/Config/DefaultGame.ini": "4e585b50ed08182eab92acaf5ce5baf6138713a161adf90bd83850003ec22033",
    "CityMaterializationProof/Config/DefaultInput.ini": "1896fc5dc59d5eb78f504ae7619fd2eb393a551b6ffcced7ab4d560c3d686bfa",
    "CityMaterializationProof/README.md": "b6bb24e880f79f125fff9dd318c5e623da0f069124cc11ee9c516e668b69446b",
    "CityMaterializationProof/Source/CityMaterializationProof.Target.cs": "9c243b7ad29c5d3b4c3b3ba645cbf14e135c5c77c70a7f8b55d057ab8a26ac52",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp": "1ab40256bf8bcbfd8464d1a7cdce5511ec97bd60fe6a496927f2de76bafcbee9",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h": "823da75aad621604cdb1b36d8668b09a37cca0bcc385e174d6d2ece3fe1051d3",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp": "7a068b41508e33de510f7301f8a9ee1248c6d09abd789e9a38cb86b354725d78",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h": "5d652be69ed6dfb05f7ec1c7857950694207db623b6e20bd2bf9f597ae04c641",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp": "32649c131810bae93c44fc54884a70ef37f7963579cb8027b9e70375cde4b4f3",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.h": "23dca5db8484a83ba33165ae594f37d7192ba2bbb1935f28b027dfaeb6266e55",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp": "892f3afd4dcda04465b024d56dd922e9f9f6b7ab35660a0f967ce5875cb04bf5",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h": "748d797af131a01833a3c00cdb405d4f97618cd8c97f0e9d1a8ea33b0a06ead9",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs": "a3de5b70766741ea0b325cc0a847261c995b03f428f327564c171eacc82b15ed",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.cpp": "a12a6f19764d880bd60bc340fb363bb4f9be7d753c639bde640bf8d9d0a0e372",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.h": "972f8f69b8fbb624b8f90ae64cc8a282d2e4d38e0915279c0dcbc7ddd73851e8",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp": "4527faf98ddb8667888f4911c2a57aa1953f7ed66ad55968fe27dba3b1ad1358",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h": "888dfa7fee0e7a66a96076a1dc3e37215f5d8bb0213f31771f593a5ad508c7c0",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h": "d4fc425030762ffa37ca8e333cb306f99fd02a74f73f50690ae3937e9c6a55b4",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp": "153b1cb3814169d2bed70e3ff3f6191681f11e05e95687c84c37834a40c3dd8b",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h": "ea7d47bc09798c7ce002ca3b99c040cb347d049f4de64ff201e4c54ef02091a8",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp": "6ef847283216bf35551fce978f367279627d68c7d845f60aa0c0683481ba8a2a",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h": "e54390475860331c014da1862bccc1b3aea0e5f3fa35824c4719a64d04f782d9",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp": "26eaf43fed3a77b68adf6f3133fe448a6ce6d91a4c21859ac19c8b2af9b2be94",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h": "75ab04322e72b2bf5c0c996e4f26d5832d570ede4495c88a2095898cb28064be",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp": "4af4db5d9d38beee9429ce3a9dc426e2e441c9e007bcc39969fba2e3df229f4d",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.h": "406663682c6b750d44a7125cb3f68a97adbbfcca22a467c6254b5cd69f0661b1",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp": "9de1d33c226c58ad3238cfbe93aa6e7719f51211cc845490327df48fc3cee9f6",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.h": "fd81e9f59dde36d7a564159140d3001b6cc4151211678608e57502749f260430",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.cpp": "549bd615b0e0811e15839762095bcd2ff288097d8c8116a42917174c3e5d2784",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.h": "b2dbb806487dd608008089b87f4019d6aa2cf4511d9fda6eb7bec0d4454d8ac5",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.cpp": "7072a6c6d26676a1b13285aded72b8db68f394e4a581c63324f292fae0693811",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.h": "afddb2cbceece7d18217f384965f2e1f9805aaf06eac9e942d08e5931a8dbfb1",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.cpp": "3063ae41be306201377fb6c905bd250ad73bb6842c4d05c6c057c60f019c9905",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.h": "ede78ca44e573e11821afb80dc6ed1b4ac0eec51300574133f5ebf51681e6931",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.cpp": "a07fc0b553c2b99d4845efc86bf778379f90816f29ae72e1251b1de6ac5f367a",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.h": "f0f9a8845439675f35a710054a62c2f4a411fbfc28507ee0af8f82f2c3908799",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.cpp": "f2360cc84101dcfdcd40e81fd74b8caf2acdff2a2a226b6fdc38fcfa823ee3f1",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.h": "b0c690d06a2380d44f20b8ae64e3707d1427af518640e43d39435b8717eca77c",
    "CityMaterializationProof/Source/CityMaterializationProofEditor.Target.cs": "b35c28f8c5a455e281f075990eda62f95d2e78dc5514ee9c52a9626d6d5f6578",
    "Cross-Domain Canonical Occupancy Materialization Proof - Draft.md": "47889ac299cf2cfbea143a6a529b1253826e74ae9ddc83f0b25903117ff9406d",
    "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md": "ecdd6f07d490e9a3f55a2a97303f5b669061220e90d640463ba0d66bdc87054c",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md": "c89b70546226bd3e15ccc0f3e9d8d03841d01b43a9b7e6c6ab9785c131b76b8c",
    "Resolution Semantics Law - v0.1.1.md": "5a696a5ee7c79a2bf2d62e34993d2863a9a127c6d02c685754c61240bc9a11aa",
    "Simultaneous Physical Domains Proof - Draft.md": "1297cdaa039d692534f2a3d133de5ad1c90d59c28578b78f6bf119750ae6be4e",
    "Simultaneous Physical Domains Proof - v0.1.1 SHA256SUMS.txt": "266b276b70c3556bd03b64b1f2438a281e76fff385bcff355e4456609e665899",
    "Simultaneous Physical Domains Proof - v0.1.1.md": "e68b33298b8973009d57d0247e85b94e9fc85ced64e1f7da68c69daa32417a28",
    "Simultaneous Physical Domains Proof Evidence - v0.1.1.md": "ea8cf7c15de1fbf95009c60a33c89afa0f1083e92002a21ac2e7e1b716449ce8",
    "THE_CITY Development Capacity and Progress Note - v0.1.11.md": "c8849fc7f54b4a67234d76a260a4dcbd3cadc71061faf450257d1c46e4444dad",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_R0.json": "59ce47bc4d6c63cbda4a740fec8d25e497ca8ed74052b16b5358745be115c2dc",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_Rfinal.json": "0b4d9d97eb166b3aae6480c5581654c39b367c3a5fab47a02daec50b1e88a181",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_Rtransit.json": "215e3383bff21a9fe01dbb240035a0fa5dd774c703417486846e027a0615a12f",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_completion_boundary_Htransit.json": "73702e173c28dd8691f4de0acf4db700b0cefd04fe738e8147fab44bcda1fb97",
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_start_boundary_H0.json": "52e2b7e94d0e57d4b9448125bdd8a41dd1cb10b9283083efe24a8756a6d86d0d",
    "proof_kernel/canonical_occupancy_transition.py": "2e3e3c652d64d5a6d44bdd8b70abb5bd431621a604e7cfa2806016e8e1f85c48",
    "proof_kernel/canonical_spatial_topology_identity.py": "326f8eec13fce85edbefcedb566fa301013bc6ca33eee2607ea4d174b60607b9",
    "proof_kernel/kernel.py": "3ae9b961d7302aa999e59c2dd87e26f0e6eb55f105f30decb3132a6d0f32e2c3",
    "proof_kernel/simultaneous_physical_domains.py": "1508973f8e9161da2f5aafd5967c7cde16dac5c3ea900d816e280777af7e0378",
    "proof_kernel/simultaneous_physical_domains_harness.py": "a5161585ae490da8cde6749521b974e501b356765366166ad05ce3dc8512cf2f",
    "proof_kernel/test_canonical_occupancy_transition.py": "aeb7e18d85e57ba5aeed94ffa9ef0ab8d449dcc41bb1fcb6a771552f3b29cad7",
    "proof_kernel/test_simultaneous_physical_domains.py": "0c40a00663abad72b7412ba5f89b84b691737a3c35dd11a44d8ee46239c40064",
    "proof_kernel/verify_canonical_occupancy_transition_release.py": "c8555329cfca5c23bf5f5d396ea47d59891660d2fa7cea6046f99fd54464a8e3",
    "proof_kernel/verify_simultaneous_physical_domains_release.py": "e931e3dc90bb4e84974b60f8310ec3793f99ad2f31fe0d443167ab74f1f15a80",
}

PRIMARY_FILES = {
    "W1": "physical_W1_A_B__A_B_witness.json",
    "W2": "physical_W2_B_A__B_A_witness.json",
    "W3": "physical_W3_A_B__B_A_witness.json",
    "W4": "physical_W4_B_A__A_B_witness.json",
}
CONTROL_FILES = {
    "C1": "control_C1_canonical_completion_independence.json",
    "C2": "control_C2_positive_Rtransit_absence.json",
    "C3": "control_C3_receipt_only_rejection.json",
    "C4a": "control_C4a_start_guard_open.json",
    "C4b": "control_C4b_completion_guard_open.json",
    "C5": "control_C5_process_replacement.json",
}
ASYMMETRIC_FILES = {
    "AF01": "failure_AF01_Rtransit_A_success_B_failure.json",
    "AF02": "failure_AF02_Rtransit_B_success_A_failure.json",
    "AF03": "failure_AF03_Rfinal_A_success_B_failure.json",
    "AF04": "failure_AF04_Rfinal_B_success_A_failure.json",
}
ASYMMETRIC_EXPECTED = {
    "AF01": ("domain_B", "refresh_0001", "beb2d2e1c574220ac31901162e58993f46108769f89394ef2df4812c9c84fc3d"),
    "AF02": ("domain_A", "refresh_0001", "13d76645353c813c480c323e380697e5f5ea24be10ab0eb80e4a3d789c060c6f"),
    "AF03": ("domain_B", "refresh_0002", "88c518da37a6311fe43a5a2cc83d56c1dd412939da716019503ee1cbb4a45b87"),
    "AF04": ("domain_A", "refresh_0002", "0c16b9a80158e78ebdd688a87335248d91b9d0843ef08a35e6ef2897825de26b"),
}
OPERATION_BY_RECORD = {"R0": "launch_0001", "Rtransit": "refresh_0001", "Rfinal": "refresh_0002"}


def _require(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def release_paths() -> tuple[str, ...]:
    paths = tuple(NON_ARTIFACT_MEMBERS) + tuple(
        f"{ARTIFACT_DIRECTORY}/{name}" for name in ARTIFACT_NAMES
    )
    _require(len(NON_ARTIFACT_MEMBERS) == 90, "90-member non-artifact closure drift")
    _require(len(CHANGED_NON_ARTIFACT_MEMBERS) == 20, "20-member change authority drift")
    _require(
        set(UNCHANGED_NON_ARTIFACT_SHA256)
        == set(NON_ARTIFACT_MEMBERS) - CHANGED_NON_ARTIFACT_MEMBERS,
        "70-member unchanged boundary drift",
    )
    _require(len(paths) == len(set(paths)) == 172 and MANIFEST not in paths,
             "frozen 172-member release closure drift")
    return tuple(sorted(paths, key=lambda value: value.encode("utf-8")))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_member(path: Path, root: Path) -> None:
    info = path.lstat()
    _require(
        stat.S_ISREG(info.st_mode) and not path.is_symlink() and info.st_nlink == 1,
        f"member is not one regular non-link file: {path}",
    )
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except ValueError as exc:
        raise ValueError(f"member realpath escapes its root: {path}") from exc


def _regular_release_member(relative: str) -> Path:
    candidate = Path(relative)
    _require(not candidate.is_absolute() and ".." not in candidate.parts,
             f"unsafe release path: {relative}")
    path = ROOT / candidate
    _regular_member(path, ROOT)
    return path


def _walk_dicts(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def visit(current: Any) -> None:
        if isinstance(current, dict):
            found.append(current)
            for child in current.values():
                visit(child)
        elif isinstance(current, list):
            for child in current:
                visit(child)

    visit(value)
    return found


def _walk_lists(value: Any) -> list[list[Any]]:
    found: list[list[Any]] = []

    def visit(current: Any) -> None:
        if isinstance(current, list):
            found.append(current)
            for child in current:
                visit(child)
        elif isinstance(current, dict):
            for child in current.values():
                visit(child)

    visit(value)
    return found


def _expected(role: str, record_role: str) -> dict[str, Any]:
    return expected_representation(
        (RECORDS / RECORD_FILENAMES[record_role]).read_bytes(),
        stored_json_bytes(projection(role, record_role)),
    )


def _record_role_from_head(head: Any) -> str:
    matches = [role for role, digest in HEAD_HASHES.items() if digest == head]
    _require(len(matches) == 1, f"unknown canonical head in live evidence: {head!r}")
    return matches[0]


def _validated_binding(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict) and set(value) == set(PROCESS_BINDING_FIELDS),
             "process binding field set drift")
    rebuilt = process_binding({key: copy.deepcopy(value[key]) for key in PROCESS_BINDING_FIELDS if key != "binding_schema"})
    _require(rebuilt == value, "process binding identity drift")
    return rebuilt


def _validate_process_evidence(value: Any) -> dict[str, Any]:
    required = {
        "bind_receipt", "binding", "bundles", "commands", "launch_plan",
        "runtime_provenance", "runtime_trace",
    }
    _require(isinstance(value, dict) and set(value) == required,
             "live process evidence member drift")
    binding = _validated_binding(value["binding"])
    role = binding["domain_role"]
    identity = operational_process_instance_id(binding)
    binding_digest = process_binding_raw_sha256(binding)

    plan = value["launch_plan"]
    _require(isinstance(plan, dict), "launch plan absent")
    for field in (
        "proof_scenario", "witness_id", "domain_role", "harness_launch_id",
        "process_root_realpath", "control_pipe_id", "structured_output_pipe_id",
        "diagnostic_pipe_id",
    ):
        _require(plan.get(field) == binding[field], f"launch plan field drift: {field}")
    _require(plan.get("launch_plan_schema") == "CrossDomainOccupancyLaunchPlan.v1",
             "launch plan schema drift")

    receipt = value["bind_receipt"]
    _require(
        receipt == {
            "bind_receipt_schema": "CrossDomainOccupancyBindReceipt.v1",
            "domain_role": role,
            "operational_process_instance_id": identity,
            "process_binding_raw_sha256": binding_digest,
            "proof_scenario": PROOF_SCENARIO,
            "state": "binding_accepted_once",
        },
        "bind receipt drift",
    )

    provenance = value["runtime_provenance"]
    _require(isinstance(provenance, dict), "runtime provenance absent")
    _require(provenance.get("audit_schema") == "CrossDomainOccupancyRuntimeProvenance.v1",
             "runtime provenance schema drift")
    _require(provenance.get("captured_before_first_materialization") is True,
             "runtime provenance timing drift")
    _require(provenance.get("proof_scenario") == PROOF_SCENARIO and provenance.get("domain_role") == role,
             "runtime provenance role drift")
    _require(provenance.get("operational_process_instance_id") == identity,
             "runtime provenance process drift")
    _require(provenance.get("process_binding_raw_sha256") == binding_digest,
             "runtime provenance binding digest drift")
    _require(provenance.get("observed_process_binding") == binding,
             "runtime provenance observed binding drift")
    verification = provenance.get("binding_verification_rows")
    _require(
        isinstance(verification, list)
        and [row.get("field") for row in verification] == list(PROCESS_BINDING_FIELDS)
        and all(row.get("matched") is True and isinstance(row.get("verification_mode"), str) for row in verification),
        "field-by-field binding verification drift",
    )
    argv = provenance.get("observed_launch_argv")
    environment = provenance.get("redacted_environment_audit")
    descriptors = provenance.get("observed_inherited_descriptor_map")
    inventory = provenance.get("project_config_and_module_inventory")
    _require(isinstance(argv, list) and sha256_bytes(canonical_json(argv).encode("utf-8")) == binding["launch_argv_raw_sha256"],
             "launch argv binding drift")
    _require(isinstance(environment, dict) and sha256_value(environment) == binding["launch_environment_audit_raw_sha256"],
             "environment audit binding drift")
    _require(environment.get("proof_semantic_key_allowlist") == [] and environment.get("plaintext_values_released") is False,
             "environment acquired semantic authority")
    _require(isinstance(descriptors, dict) and sha256_value(descriptors) == binding["inherited_descriptor_map_raw_sha256"],
             "descriptor-map binding drift")
    _require(isinstance(inventory, dict) and sha256_value(inventory) == binding["project_config_and_module_inventory_raw_sha256"],
             "project inventory binding drift")
    loaded = provenance.get("loaded_image_inventory")
    _require(
        isinstance(loaded, list) and loaded
        and all(type(row.get("filesystem_regular_file")) is bool
                and str(row.get("realpath", "")).startswith("/")
                and str(row.get("reported_path", "")).startswith("/") for row in loaded)
        and any(row.get("filesystem_regular_file") is True for row in loaded),
        "loaded-image inventory drift",
    )
    actors = provenance.get("initial_world_actor_class_inventory")
    _require(
        isinstance(actors, list) and actors
        and all(type(row.get("actor_count")) is int and row["actor_count"] > 0 for row in actors)
        and not any(str(row.get("class_path", "")).endswith("Pawn") for row in actors),
        "initial zero-Pawn actor inventory drift",
    )
    descriptor_rows = provenance.get("descriptor_kernel_identities")
    _require(isinstance(descriptor_rows, list) and [row.get("fd") for row in descriptor_rows] == [0, 1, 2],
             "descriptor kernel identity drift")

    commands = value["commands"]
    _require(isinstance(commands, list) and commands and commands[0] == bind_invocation(binding),
             "stdin command binding drift")
    command_sequences = [row.get("command_sequence") for row in commands if type(row.get("command_sequence")) is int]
    _require(command_sequences == list(range(len(command_sequences))), "stdin command sequence drift")

    bundles = value["bundles"]
    _require(isinstance(bundles, dict), "bundle inventory absent")
    for operation_id, bundle in bundles.items():
        _require((role, operation_id) in OPERATION_ROWS and isinstance(bundle, dict),
                 "unknown live bundle")
        row = OPERATION_ROWS[(role, operation_id)]
        expected_names = [row["payload_file"], row["projection_file"], row["invocation_file"]]
        _require(bundle.get("names") == expected_names, "bundle member-name drift")
        expected_invocation = operation_invocation(role, operation_id, identity)
        _require(bundle.get("operation_invocation") == expected_invocation,
                 "operation invocation drift")
        inventory_value = bundle.get("inventory")
        files = inventory_value.get("files") if isinstance(inventory_value, dict) else None
        _require(isinstance(files, list) and [entry.get("filename") for entry in files] == expected_names,
                 "bundle inventory order drift")
        expected_digests = [
            RAW_HASHES[row["target_role"]],
            PROJECTION_ROWS[(role, row["target_role"])]["raw_sha256"],
            sha256_value(expected_invocation),
        ]
        actual_digests = [entry.get("raw_sha256") for entry in files]
        if actual_digests != expected_digests:
            frozen_asymmetric_digests = {row[2] for row in ASYMMETRIC_EXPECTED.values()}
            _require(
                actual_digests[0] == expected_digests[0]
                and actual_digests[2] == expected_digests[2]
                and actual_digests[1] in frozen_asymmetric_digests,
                "bundle byte identity drift",
            )
        _require(all(entry.get("link_count") == 1 and type(entry.get("size")) is int and entry["size"] > 0 for entry in files),
                 "bundle regular-file identity drift")

    traces = value["runtime_trace"]
    _require(isinstance(traces, list) and traces, "runtime trace absent")
    _require([row.get("trace_sequence") for row in traces] == list(range(len(traces))),
             "runtime trace sequence drift")
    for row in traces:
        _require(row.get("trace_schema") == "CrossDomainOccupancyRuntimeTraceEvent.v1",
                 "runtime trace schema drift")
        _require(row.get("proof_scenario", PROOF_SCENARIO) == PROOF_SCENARIO,
                 "runtime trace scenario drift")
        _require(row.get("domain_role") == role and row.get("operational_process_instance_id") == identity,
                 "runtime trace process drift")
        _require(row.get("process_binding_raw_sha256") == binding_digest,
                 "runtime trace binding drift")
        _require(row.get("monotonic_process_local_counter") == row.get("trace_sequence"),
                 "runtime trace counter drift")
        _require(row.get("stage_edge") in {"entered", "completed", "rejected", "fault_injected"},
                 "runtime trace edge drift")
        output = row.get("output_identity")
        _require(output is None or (isinstance(output, dict) and is_sha256(output.get("raw_sha256"))),
                 "runtime trace output identity drift")
    return binding


def _validate_live_observation(value: Any, binding: Mapping[str, Any] | None = None) -> None:
    _require(isinstance(value, dict) and value.get("observation_schema") == LIVE_OBSERVATION_SCHEMA,
             "live observation schema drift")
    counts = (
        ("proof_relevant_actor_count", "proof_relevant_actor_rows"),
        ("anchor_actor_count", "anchor_actor_rows"),
        ("subject_actor_count", "subject_actor_rows"),
        ("route_actor_count", "route_actor_rows"),
        ("unexpected_proof_tagged_actor_count", "unexpected_proof_tagged_actor_rows"),
        ("pawn_count", "pawn_rows"),
        ("controller_count", "controller_rows"),
        ("auto_receive_input_actor_count", "auto_receive_input_actor_rows"),
        ("phase_4_actor_input_binding_count", "phase_4_actor_input_binding_rows"),
    )
    for count, rows in counts:
        _require(type(value.get(count)) is int and isinstance(value.get(rows), list) and value[count] == len(value[rows]),
                 f"live observation count drift: {count}")
    _require(value.get("proof_scenario") == PROOF_SCENARIO, "live observation scenario drift")
    _require(value.get("world_package_name") == "/Engine/Maps/Entry" and value.get("world_type") == "Game",
             "live observation world drift")
    _require(value.get("observation_source") == "exhaustive_live_ue_world_census",
             "live observation source drift")
    _require(
        value.get("route_actor_count") == 0
        and value.get("unexpected_proof_tagged_actor_count") == 0
        and value.get("pawn_count") == 0
        and value.get("controller_count") == 1
        and value.get("auto_receive_input_actor_count") == 0
        and value.get("phase_4_actor_input_binding_count") == 0,
        "live isolation boundary drift",
    )
    _require(value.get("proof_relevant_actor_count") == value.get("anchor_actor_count") + value.get("subject_actor_count"),
             "proof-relevant census cardinality drift")
    union = sorted(value["anchor_actor_rows"] + value["subject_actor_rows"], key=lambda row: row.get("actor_path", ""))
    _require(value["proof_relevant_actor_rows"] == union, "proof-relevant actor union drift")
    actor_paths = [row.get("actor_path") for row in union]
    _require(None not in actor_paths and len(actor_paths) == len(set(actor_paths)),
             "live actor identity collision")
    controller = value["controller_rows"][0]
    _require(
        controller.get("actor_class") == "/Script/Engine.PlayerController"
        and controller.get("pawn_path") is None
        and controller.get("phase_4_handler_reachable") is False,
        "inert controller boundary drift",
    )
    if binding is not None:
        _require(value.get("domain_role") == binding["domain_role"], "live observation role drift")
        _require(value.get("operational_process_instance_id") == operational_process_instance_id(binding),
                 "live observation process drift")
        _require(value.get("process_binding_raw_sha256") == process_binding_raw_sha256(binding),
                 "live observation binding drift")


def _validate_liveness_observation(value: Any, binding: Mapping[str, Any]) -> None:
    _require(value.get("liveness_observation_schema") == "CrossDomainOccupancyLivenessObservation.v1",
             "liveness observation schema drift")
    _require(value.get("proof_scenario") == PROOF_SCENARIO and value.get("observation_source") == "independent_harness_os_monitor",
             "liveness observation source drift")
    _require(value.get("domain_role") == binding["domain_role"], "liveness role drift")
    _require(value.get("operational_process_instance_id") == operational_process_instance_id(binding),
             "liveness process drift")
    _require(value.get("process_binding_raw_sha256") == process_binding_raw_sha256(binding),
             "liveness binding drift")
    _require(value.get("observed_pid") == binding["pid"] and value.get("observed_macos_process_start") == binding["macos_process_start"],
             "liveness OS identity drift")
    _require(type(value.get("replacement_spawn_count")) is int and value["replacement_spawn_count"] >= 0,
             "liveness replacement count drift")
    for field in (
        "original_child_handle_exit_observed", "wait_status_available",
        "control_pipe_unexpected_eof", "structured_output_pipe_unexpected_eof",
        "process_start_pair_changed",
    ):
        _require(type(value.get(field)) is bool, f"liveness boolean drift: {field}")


def _validate_head_observation(value: Any) -> None:
    _require(value.get("observation_schema") == HEAD_OBSERVATION_SCHEMA,
             "canonical head observation schema drift")
    role = value.get("source_record_role")
    _require(role in ("Rtransit", "Rfinal"), "canonical head role drift")
    expected_row = guard_and_head_observation_matrix()["head_observations"][0 if role == "Rtransit" else 1]
    for field, expected_value in expected_row.items():
        _require(value.get(field) == expected_value, f"canonical head field drift: {field}")
    _require(value.get("publication_state") == "harness_private_verified", "canonical head publication drift")
    _require(value.get("source_record_mode") == "regular_file_only", "canonical head file-mode drift")
    _require(str(value.get("source_record_realpath", "")).endswith(RECORD_FILENAMES[role]),
             "canonical head source path drift")
    _require(type(value.get("source_record_size")) is int and value["source_record_size"] > 0,
             "canonical head source size drift")


def _validate_harness_trace(rows: list[Any]) -> None:
    _require([row.get("trace_sequence") for row in rows] == list(range(len(rows))),
             "harness trace sequence drift")
    for row in rows:
        _require(row.get("harness_trace_schema") == "CrossDomainOccupancyHarnessTraceEvent.v1",
                 "harness trace schema drift")
        _require(row.get("stage_edge") in {"entered", "completed", "fault_injected", "failure_observed"},
                 "harness trace edge drift")
        _require(is_sha256(row.get("canonical_before_after_snapshot_raw_sha256")),
                 "harness trace canonical digest drift")


def _validate_disposition(value: Mapping[str, Any]) -> None:
    try:
        validate_head_disposition(value)
        return
    except Exception:
        pass
    _require(value.get("disposition_schema") == "CrossDomainOccupancyHeadDisposition.v1",
             "non-matrix disposition schema drift")
    _require((value.get("head_state"), value.get("head_relation")) in {
                 ("invalid", "untrusted"), ("protocol_invalid", "untrusted"),
                 ("unbound", "none"),
             }
             and isinstance(value.get("reason_code"), str) and value.get("reason_code"),
             "non-matrix disposition was not fail-closed")
    for field in (
        "current_head_representation_claim_enabled", "refresh_enabled", "inspection_enabled",
        "local_nonconsequential_step_enabled", "local_publication_enabled",
        "canonical_completion_enabled", "canonical_evidence_enabled", "canonical_mutation_enabled",
        "canonical_scheduling_enabled", "canonical_truth_publication_enabled", "peer_interaction_enabled",
    ):
        _require(value.get(field) is False, f"fail-closed disposition enabled {field}")
    _require(value.get("diagnostics_enabled") is True and value.get("termination_enabled") is True,
             "fail-closed disposition disabled diagnosis or termination")


def _validate_embedded_runtime(value: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    bindings: dict[str, dict[str, Any]] = {}
    processes = value.get("domain_processes")
    if isinstance(processes, dict):
        for process in processes.values():
            binding = _validate_process_evidence(process)
            identity = operational_process_instance_id(binding)
            _require(identity not in bindings, "duplicate process identity within occurrence")
            bindings[identity] = binding
    replacement = value.get("replacement_process")
    if isinstance(replacement, dict):
        if isinstance(replacement.get("nominal_binding"), dict):
            binding = _validated_binding(replacement["nominal_binding"])
            submitted = _validated_binding(replacement.get("binding"))
            _require(
                binding != submitted
                and replacement.get("bind_receipt") is None
                and replacement.get("runtime_provenance") is None
                and replacement.get("runtime_trace") == []
                and replacement.get("bundles") == {}
                and replacement.get("commands") == [bind_invocation(submitted)],
                "unbound copied-label replacement evidence drift",
            )
            plan = replacement.get("launch_plan")
            _require(isinstance(plan, dict)
                     and plan.get("process_root_realpath") == binding["process_root_realpath"]
                     and plan.get("domain_role") == binding["domain_role"],
                     "unbound replacement launch-plan drift")
        else:
            binding = _validate_process_evidence(replacement)
        identity = operational_process_instance_id(binding)
        _require(identity not in bindings, "replacement reused original process identity")
        bindings[identity] = binding

    dictionaries = _walk_dicts(value)
    exact_chain = canonical_chain()
    receipts = [row for row in dictionaries if row.get("receipt_schema") == MATERIALIZATION_RECEIPT_SCHEMA]
    observations = [row for row in dictionaries if row.get("observation_schema") == LIVE_OBSERVATION_SCHEMA]
    receipt_digests = {sha256_value(row) for row in receipts}
    observation_digests = {sha256_value(row) for row in observations}
    expected_digests: set[str] = set()
    for binding in bindings.values():
        for record_role in RECORD_ROLES:
            expected_digests.add(sha256_value(_expected(binding["domain_role"], record_role)))

    for row in dictionaries:
        if row.get("chain_schema") == "CrossDomainOccupancyCanonicalChain.v1":
            _require(row == exact_chain, "sealed canonical chain changed in live occurrence")
        if row.get("receipt_schema") == MATERIALIZATION_RECEIPT_SCHEMA:
            identity = row.get("operational_process_instance_id")
            _require(identity in bindings, "receipt lacks registered live process")
            binding = bindings[identity]
            record_role = _record_role_from_head(row.get("accepted_canonical_hash"))
            operation_id = OPERATION_BY_RECORD[record_role]
            validate_materialization_receipt(row, _expected(binding["domain_role"], record_role), binding, operation_id)
            _require(row.get("operation_id") == operation_id, "receipt operation drift")
        elif row.get("observation_schema") == LIVE_OBSERVATION_SCHEMA:
            identity = row.get("operational_process_instance_id")
            _require(identity in bindings, "observation lacks registered live process")
            _validate_live_observation(row, bindings[identity])
        elif row.get("disposition_schema") == "CrossDomainOccupancyHeadDisposition.v1":
            _validate_disposition(row)
            identity = row.get("operational_process_instance_id")
            _require(identity in bindings, "disposition lacks registered live process")
            binding = bindings[identity]
            _require(row.get("process_binding_raw_sha256") == process_binding_raw_sha256(binding),
                     "disposition binding drift")
            for field, allowed in (
                ("expected_representation_raw_sha256", expected_digests),
                ("materialization_receipt_raw_sha256", receipt_digests),
                ("live_observation_raw_sha256", observation_digests),
            ):
                _require(row.get(field) is None or row[field] in allowed,
                         f"disposition detached digest drift: {field}")
        elif row.get("liveness_observation_schema") == "CrossDomainOccupancyLivenessObservation.v1":
            identity = row.get("operational_process_instance_id")
            _require(identity in bindings, "liveness observation lacks registered process")
            _validate_liveness_observation(row, bindings[identity])
        elif row.get("observation_schema") == HEAD_OBSERVATION_SCHEMA:
            _validate_head_observation(row)
        elif "diagnostic_schema" in row:
            _require(
                row.get("diagnostic_schema") in {
                    "CrossDomainOccupancyFailure.v1", "CrossDomainOccupancyHarnessFailure.v1",
                }
                and isinstance(row.get("reason_code"), str)
                and isinstance(row.get("stage_id"), str),
                "failure diagnostic drift",
            )

    for observation in observations:
        matches = [
            receipt for receipt in receipts
            if receipt.get("operational_process_instance_id") == observation.get("operational_process_instance_id")
            and receipt.get("publication_generation") == observation.get("observed_publication_generation")
        ]
        if matches:
            _require(len({sha256_value(row) for row in matches}) == 1,
                     "ambiguous live receipt relation")
            receipt = matches[0]
            binding = bindings[observation["operational_process_instance_id"]]
            record_role = _record_role_from_head(receipt["accepted_canonical_hash"])
            compare_expectation_receipt_observation(
                _expected(binding["domain_role"], record_role), receipt, observation,
                binding, OPERATION_BY_RECORD[record_role],
            )

    for rows in _walk_lists(value):
        if rows and all(isinstance(row, dict) and row.get("harness_trace_schema") == "CrossDomainOccupancyHarnessTraceEvent.v1" for row in rows):
            _validate_harness_trace(rows)
    terminations = value.get("terminations")
    if isinstance(terminations, dict):
        known_pids = {binding["pid"] for binding in bindings.values()}
        for termination in terminations.values():
            _require(termination.get("terminated") is True and termination.get("pid") in known_pids,
                     "termination witness drift")
    return bindings


def _validate_primary(
    witness: Any,
    witness_name: str,
    values: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    _require(isinstance(witness, dict), f"{witness_name} witness absent")
    expected_id = {
        "W1": "w1_A_B__A_B", "W2": "w2_B_A__B_A",
        "W3": "w3_A_B__B_A", "W4": "w4_B_A__A_B",
    }[witness_name]
    _require(witness.get("witness_schema") == "CrossDomainOccupancyPrimaryWitness.v1",
             f"{witness_name} witness schema drift")
    _require(witness.get("proof_scenario") == PROOF_SCENARIO and witness.get("witness_id") == expected_id,
             f"{witness_name} witness identity drift")
    _require(witness.get("canonical_chain") == canonical_chain(),
             f"{witness_name} canonical chain drift")
    expected_orders = PRIMARY_REFRESH_ORDERS[witness_name]
    _require(
        witness.get("refresh_orders") == {
            "Rtransit": list(expected_orders[0]), "Rfinal": list(expected_orders[1]),
        },
        f"{witness_name} refresh-order drift",
    )
    _require(witness.get("guard_history") == [
        "open_for_R0", "closed_for_R0_to_Rtransit", "open_for_Rtransit",
        "closed_for_Rtransit_to_Rfinal", "open_for_Rfinal",
    ], f"{witness_name} guard history drift")
    bindings = _validate_embedded_runtime(witness)
    _require(len(bindings) == 2, f"{witness_name} original process count drift")
    process_rows = witness.get("domain_processes")
    _require(isinstance(process_rows, dict) and set(process_rows) == set(DOMAIN_ROLES),
             f"{witness_name} domain process role drift")
    births = [canonical_json(binding["macos_process_start"]) for binding in bindings.values()]
    roots = [binding["process_root_realpath"] for binding in bindings.values()]
    _require(len(set(births)) == 2 and len(set(roots)) == 2,
             f"{witness_name} process isolation drift")

    receipts = witness.get("receipts")
    observations = witness.get("observations")
    expectations = witness.get("expectations")
    dispositions = witness.get("dispositions")
    for container, label in (
        (receipts, "receipts"), (observations, "observations"),
        (expectations, "expectations"), (dispositions, "dispositions"),
    ):
        _require(isinstance(container, dict) and set(container) == set(DOMAIN_ROLES),
                 f"{witness_name} {label} role drift")
    for role in DOMAIN_ROLES:
        binding = process_rows[role]["binding"]
        _require(set(receipts[role]) == set(RECORD_ROLES), f"{witness_name}/{role} receipt role drift")
        _require(set(expectations[role]) == set(RECORD_ROLES), f"{witness_name}/{role} expectation role drift")
        _require(set(dispositions[role]) == set(RECORD_ROLES), f"{witness_name}/{role} disposition role drift")
        for record_role in RECORD_ROLES:
            expected = _expected(role, record_role)
            receipt = receipts[role][record_role]
            observation = observations[role][record_role]
            disposition = dispositions[role][record_role]
            _require(expectations[role][record_role] == expected,
                     f"{witness_name}/{role}/{record_role} independent expectation drift")
            validate_materialization_receipt(
                receipt, expected, binding, OPERATION_BY_RECORD[record_role]
            )
            _validate_live_observation(observation, binding)
            compare_expectation_receipt_observation(
                expected, receipt, observation, binding, OPERATION_BY_RECORD[record_role]
            )
            validate_head_disposition(disposition)
            _require(
                disposition.get("head_state") == "synchronized"
                and disposition.get("head_relation") == "current"
                and disposition.get("represented_canonical_hash") == HEAD_HASHES[record_role]
                and disposition.get("harness_observed_current_canonical_hash") == HEAD_HASHES[record_role]
                and disposition.get("expected_representation_raw_sha256") == sha256_value(expected)
                and disposition.get("materialization_receipt_raw_sha256") == sha256_value(receipt)
                and disposition.get("live_observation_raw_sha256") == sha256_value(observation),
                f"{witness_name}/{role}/{record_role} synchronized disposition drift",
            )
            if values is not None:
                letter = role[-1]
                receipt_name = f"physical_{witness_name}_domain_{letter}_{record_role}_materialization_receipt.json"
                observation_name = f"physical_{witness_name}_domain_{letter}_{record_role}_live_observation.json"
                _require(values.get(receipt_name) == receipt, f"{receipt_name} detached relation drift")
                _require(values.get(observation_name) == observation, f"{observation_name} detached relation drift")

    checkpoints = witness.get("checkpoints")
    _require(isinstance(checkpoints, list) and [row.get("checkpoint_id") for row in checkpoints] == [f"L{i}" for i in range(9)],
             f"{witness_name} checkpoint closure drift")
    for number, checkpoint in enumerate(checkpoints):
        _require(checkpoint.get("original_process_count") == 2, f"{witness_name}/L{number} process count drift")
        domain_observations = checkpoint.get("domain_observations")
        _require(isinstance(domain_observations, dict) and set(domain_observations) == set(DOMAIN_ROLES),
                 f"{witness_name}/L{number} liveness role drift")
        for role in DOMAIN_ROLES:
            _validate_liveness_observation(domain_observations[role], process_rows[role]["binding"])
            _require(domain_observations[role].get("checkpoint_id") == f"L{number}",
                     f"{witness_name}/L{number}/{role} checkpoint drift")

    heads = witness.get("head_publications")
    _require(isinstance(heads, dict) and set(heads) == {"Rtransit", "Rfinal"},
             f"{witness_name} head publication closure drift")
    for record_role, head in heads.items():
        _validate_head_observation(head["observation"])
        _require(head.get("observation_raw_sha256") == sha256_value(head["observation"]),
                 f"{witness_name}/{record_role} head digest drift")
        _validate_harness_trace(head["trace"])

    if values is not None:
        liveness = values[f"physical_{witness_name}_liveness_witness.json"]
        _require(liveness == {
            "checkpoints": witness["checkpoints"],
            "proof_scenario": PROOF_SCENARIO,
            "result": "PASS",
            "terminations": witness["terminations"],
            "witness_id": expected_id,
        }, f"{witness_name} detached liveness relation drift")
    return bindings


def _validate_controls(values: Mapping[str, Any]) -> None:
    expected_histories = {
        "C1": ["open_for_R0", "closed_for_R0_to_Rtransit", "open_for_Rtransit", "closed_for_c1_Rtransit_to_Rfinal"],
        "C2": ["open_for_R0", "closed_for_R0_to_Rtransit", "open_for_Rtransit"],
        "C3": ["open_for_R0", "closed_for_R0_to_Rtransit", "open_for_Rtransit"],
        "C4a": ["open_for_R0", "failed_closed"],
        "C4b": ["open_for_R0", "closed_for_R0_to_Rtransit", "open_for_Rtransit", "failed_closed"],
        "C5": ["open_for_R0", "closed_for_R0_to_Rtransit", "open_for_Rtransit"],
    }
    for case_id, filename in CONTROL_FILES.items():
        case = values[filename]
        _require(case.get("case_id") == case_id and case.get("proof_scenario") == PROOF_SCENARIO,
                 f"{case_id} identity drift")
        _require(case.get("canonical_before") == case.get("canonical_after") == canonical_chain(),
                 f"{case_id} changed canonical authority")
        _require(case.get("guard_history") == expected_histories[case_id],
                 f"{case_id} guard history drift")
        bindings = _validate_embedded_runtime(case)
        _require(len(bindings) == (3 if case_id == "C5" else 2), f"{case_id} process count drift")
        if case_id == "C1":
            _require(all(row.get("head_state") == "stale" and row.get("head_relation") == "two_generation_stale"
                         for row in case["terminal_dispositions"].values()), "C1 completion independence drift")
            _validate_head_observation(case["start_head"]["observation"])
            _validate_head_observation(case["completion_head"]["observation"])
        elif case_id in ("C2", "C3"):
            expected_counts = (0, 0) if case_id == "C2" else (1, 1)
            observation = case["terminal_live_observation"]
            _require((observation["anchor_actor_count"], observation["subject_actor_count"]) == expected_counts,
                     f"{case_id} terminal census drift")
            expected_stage = "M20_spawn_configure_and_finish_target_anchor" if case_id == "C2" else "M16_validate_candidate_coherence_and_cardinality"
            expected_edge = "before" if case_id == "C2" else "after"
            _require(case["failure"].get("stage_id") == expected_stage
                     and case["failure"].get("reason_code") == f"injected_{expected_stage}_{expected_edge}",
                     f"{case_id} exact fault drift")
            _require((case.get("receipt_only_candidate") is None) == (case_id == "C2"),
                     f"{case_id} receipt-only control drift")
            _require(case["resulting_disposition"].get("head_state") == "invalid",
                     f"{case_id} did not fail closed")
        elif case_id == "C4a":
            _require(all(row.get("head_state") == "protocol_invalid" for row in case["terminal_dispositions"].values()),
                     "C4a guard independence drift")
        elif case_id == "C4b":
            _require(all(row.get("observed_publication_generation") == "publication_0002"
                         for row in case["terminal_observations"].values()),
                     "C4b completion guard control drift")
        else:
            original = case["domain_processes"]["domain_B"]["binding"]
            replacement = case["replacement_process"]["binding"]
            _require(case.get("replacement_rejected_as_continuity") is True,
                     "C5 replacement continuity was accepted")
            _require(
                operational_process_instance_id(original) != operational_process_instance_id(replacement)
                and original["macos_process_start"] != replacement["macos_process_start"]
                and original["process_root_realpath"] != replacement["process_root_realpath"],
                "C5 replacement identity drift",
            )


def _validate_asymmetric(values: Mapping[str, Any]) -> None:
    for case_id, filename in ASYMMETRIC_FILES.items():
        case = values[filename]
        failed_role, operation_id, malformed_digest = ASYMMETRIC_EXPECTED[case_id]
        successful_role = "domain_A" if failed_role == "domain_B" else "domain_B"
        _require(case.get("case_id") == case_id and case.get("failed_role") == failed_role,
                 f"{case_id} failed-role drift")
        _require(case.get("successful_role") == successful_role and case.get("operation_id") == operation_id,
                 f"{case_id} successful-role or operation drift")
        _require(case.get("canonical_before") == case.get("canonical_after") == canonical_chain(),
                 f"{case_id} changed canonical authority")
        _require(case["failure"].get("reason_code") == "projection_raw_sha256_not_frozen"
                 and case["failure"].get("stage_id") == "materialization",
                 f"{case_id} rejection stage drift")
        failed_bundle = case["failed_bundle"]
        malformed_raw = failed_bundle["malformed_projection_canonical_json"].encode("utf-8")
        _require(sha256_bytes(malformed_raw) == malformed_digest
                 and failed_bundle.get("malformed_projection_raw_sha256") == malformed_digest,
                 f"{case_id} malformed projection byte drift")
        strict_load_stored_json(malformed_raw)
        bindings = _validate_embedded_runtime(case)
        _require(len(bindings) == 2, f"{case_id} process count drift")
        failed_trace = case["domain_processes"][failed_role]["runtime_trace"]
        m09_edges = [
            row["stage_edge"] for row in failed_trace
            if row.get("operation_id") == operation_id
            and row.get("stage_id") == "M09_authenticate_and_validate_projection"
        ]
        _require(m09_edges == ["entered"], f"{case_id} did not stop inside exact M09 edge")
        predecessor = "R0" if operation_id == "refresh_0001" else "Rtransit"
        expected = _expected(failed_role, predecessor)
        failed_observation = case["failed_domain_observation"]
        _require(failed_observation["anchor_actor_count"] == 1
                 and failed_observation["subject_actor_count"] == expected["expected_subject_actor_count"],
                 f"{case_id} predecessor retention drift")


def _validate_binding_adversaries(value: Any) -> None:
    _require(value.get("adversary_schema") == "CrossDomainOccupancyProcessBindingAdversaries.v1",
             "process-binding adversary schema drift")
    _require(value.get("case_count") == 23 and value.get("logical_field_order") == list(PROCESS_BINDING_FIELDS),
             "PB01-PB23 closure drift")
    cases = value.get("cases")
    _require(isinstance(cases, list) and [row.get("case_id") for row in cases] == [f"PB{i:02d}" for i in range(1, 24)],
             "PB01-PB23 identity drift")
    for number, case in enumerate(cases, 1):
        nominal = _validated_binding(case.get("nominal_binding"))
        submitted = case.get("submitted_binding")
        _require(isinstance(submitted, dict) and submitted != nominal,
                 f"PB{number:02d} mutation absent")
        if number <= 22:
            field = PROCESS_BINDING_FIELDS[number - 1]
            changed = [key for key in set(nominal) | set(submitted) if nominal.get(key) != submitted.get(key)]
            _require(changed == [field] and case.get("changed_fields") == [field],
                     f"PB{number:02d} field isolation drift")
            expected_reason = "binding_structure_mismatch" if number <= 2 else f"binding_field_mismatch_{field}"
        else:
            _require(case.get("changed_fields") == ["witness_id", "harness_launch_id", "copied_evidence_labels"],
                     "PB23 copied-label field set drift")
            expected_reason = "binding_field_mismatch_harness_launch_id"
        _require(case["failure"].get("reason_code") == expected_reason
                 and case["failure"].get("stage_id") == "binding",
                 f"PB{number:02d} rejection drift")
        _require(case.get("runtime_trace") == [] and case.get("canonical_before") == case.get("canonical_after") == canonical_chain(),
                 f"PB{number:02d} reached materialization or changed canonical state")
        _require(case["termination"].get("terminated") is True
                 and case["termination"].get("pid") == nominal["pid"],
                 f"PB{number:02d} termination drift")


def _validate_authority_adversaries(value: Any) -> None:
    _require(value.get("authority_adversaries_schema") == "CrossDomainOccupancyAuthorityAdversaries.v1",
             "authority adversary schema drift")
    _require(value.get("case_count") == 40 and value.get("subcase_count") == 121,
             "A01-A40 / 121 closure drift")
    cases = value.get("cases")
    _require(isinstance(cases, list) and [row.get("case_id") for row in cases] == [f"A{i:02d}" for i in range(1, 41)],
             "A01-A40 ordering drift")
    expected_subcase = 0
    for case in cases:
        case_id = case["case_id"]
        action, variants, stage, reason, terminal = AUTHORITY_ROWS[case_id]
        _require(case.get("action_id") == action and case.get("subcase_count") == len(variants),
                 f"{case_id} action/variant closure drift")
        subcases = case.get("subcases")
        _require(isinstance(subcases, list) and len(subcases) == len(variants),
                 f"{case_id} subcase closure drift")
        for variant, subcase in zip(variants, subcases):
            expected_subcase += 1
            expected_action = action if not variant else f"{action}/{variant}"
            _require(subcase.get("subcase_id") == f"AS{expected_subcase:03d}"
                     and subcase.get("action_id") == expected_action,
                     f"{case_id} subcase identity drift")
            _require(subcase.get("expected_rejecting_stage") == stage
                     and subcase.get("actual_rejecting_stage") == stage
                     and subcase.get("expected_reason_code") == reason
                     and subcase.get("actual_rejection_reason") == reason,
                     f"{case_id}/{variant or 'single'} did not reject at the frozen reason")
            boundary = subcase.get("concrete_execution", {}).get("authority_boundary_rejection", {})
            _require(boundary.get("actual_rejecting_stage") == stage
                     and boundary.get("actual_reason_code") == reason
                     and isinstance(boundary.get("underlying_reason_code"), str)
                     and boundary.get("underlying_reason_code"),
                     f"{case_id}/{variant or 'single'} mechanical boundary witness drift")
            _require(subcase.get("result") == "REJECTED"
                     and subcase.get("terminal_physical_disposition") == terminal,
                     f"{case_id}/{variant or 'single'} rejection disposition drift")
            _require(subcase.get("canonical_before") == subcase.get("canonical_after") == canonical_chain(),
                     f"{case_id}/{variant or 'single'} changed canonical authority")
    _require(expected_subcase == 121, "authority subcase numbering drift")


def _validate_head_faults(value: Any) -> None:
    _require(value.get("fault_matrix_schema") == "CrossDomainOccupancyHeadPublicationFaultAtomicity.v1",
             "head-publication fault schema drift")
    _require(value.get("case_count") == 18 and value.get("stage_order") == list(HEAD_PUBLICATION_STAGES),
             "HF01-HF18 closure drift")
    cases = value.get("cases")
    _require(isinstance(cases, list) and [row.get("case_id") for row in cases] == [f"HF{i:02d}" for i in range(1, 19)],
             "HF01-HF18 identity drift")
    for number, case in enumerate(cases, 1):
        stage_index = (number - 1) % len(HEAD_PUBLICATION_STAGES)
        stage = HEAD_PUBLICATION_STAGES[stage_index]
        head_kind = "start" if number <= 9 else "completion"
        fault = case["fault"]
        _require(case.get("canonical_before") == case.get("canonical_after") == canonical_chain(),
                 f"HF{number:02d} changed canonical authority")
        _require(case.get("head_fault_case_schema") == "CrossDomainOccupancyHeadPublicationFaultCase.v1",
                 f"HF{number:02d} schema drift")
        _require(fault.get("stage_id") == stage and fault.get("head_kind") == head_kind,
                 f"HF{number:02d} stage/head drift")
        plan = fault["fault_plan"]
        arm = fault["arm_receipt"]
        _require(plan.get("case_id") == case["case_id"] and plan.get("stage_id") == stage and plan.get("edge") == "after",
                 f"HF{number:02d} plan drift")
        _require(arm.get("harness_fault_plan_raw_sha256") == sha256_value(plan)
                 and arm.get("stage_id") == stage and arm.get("arm_state") == "armed_once",
                 f"HF{number:02d} arm receipt drift")
        trace = fault["harness_trace"]
        _validate_harness_trace(trace)
        _require(len(trace) == 2 * (stage_index + 1) + 1
                 and trace[-1].get("stage_id") == stage
                 and trace[-1].get("stage_edge") == "fault_injected",
                 f"HF{number:02d} exact trace prefix drift")
        uncertain = stage_index >= HEAD_PUBLICATION_STAGES.index("atomic_publish")
        published = stage_index >= HEAD_PUBLICATION_STAGES.index("atomic_publish")
        _require(fault.get("publication_uncertain") is uncertain
                 and fault.get("head_observation_published") is published,
                 f"HF{number:02d} atomic publication outcome drift")
        if fault.get("head_observation_candidate") is not None:
            _validate_head_observation(fault["head_observation_candidate"])
        expected_guard = "failed_closed" if uncertain else (
            "closed_for_R0_to_Rtransit" if head_kind == "start" else "closed_for_Rtransit_to_Rfinal"
        )
        _require(case.get("terminal_guard_state") == expected_guard,
                 f"HF{number:02d} fail-closed guard drift")
        _require(len(_validate_embedded_runtime(case)) == 2,
                 f"HF{number:02d} process count drift")


def _validate_materialization_faults(value: Any) -> None:
    _require(value.get("fault_matrix_schema") == "CrossDomainOccupancyMaterializationFaultAtomicity.v1",
             "materialization fault schema drift")
    _require(
        value.get("case_count") == 138
        and value.get("stage_order") == list(MATERIALIZATION_STAGES)
        and value.get("context_order") == [row[0] for row in MATERIALIZATION_CONTEXTS]
        and value.get("edge_order") == ["before", "after"],
        "MF001-MF138 matrix closure drift",
    )
    cases = value.get("cases")
    _require(isinstance(cases, list) and [row.get("case_id") for row in cases] == [f"MF{i:03d}" for i in range(1, 139)],
             "MF001-MF138 identity drift")
    number = 0
    for context, role, operation_id, record_role in MATERIALIZATION_CONTEXTS:
        for stage_index, stage in enumerate(MATERIALIZATION_STAGES):
            for edge in ("before", "after"):
                case = cases[number]
                number += 1
                label = case["case_id"]
                _require(
                    case.get("context") == context and case.get("target_role") == role
                    and case.get("operation_id") == operation_id
                    and case.get("stage_id") == stage and case.get("edge") == edge,
                    f"{label} cross-product coordinate drift",
                )
                _require(case.get("canonical_before") == case.get("canonical_after") == canonical_chain(),
                         f"{label} changed canonical authority")
                failure = case["failure"]
                _require(failure.get("fault_injected") is True
                         and failure.get("stage_id") == stage
                         and failure.get("reason_code") == f"injected_{stage}_{edge}",
                         f"{label} compiled rejection drift")
                arm = case["arm_invocation"]
                arm_receipt = case["arm_receipt"]
                _require(arm.get("case_id") == label and arm.get("stage_id") == stage
                         and arm.get("edge") == edge and arm.get("armed_operation_id") == operation_id,
                         f"{label} arm invocation drift")
                _require(arm_receipt.get("case_id") == label and arm_receipt.get("stage_id") == stage
                         and arm_receipt.get("edge") == edge and arm_receipt.get("arm_state") == "armed_once",
                         f"{label} arm receipt drift")
                entered = stage_index >= MATERIALIZATION_STAGES.index("M17_begin_publication_linearization_interval")
                _require(case.get("publication_interval_entered") is entered
                         and case.get("post_fault_census_available") is False,
                         f"{label} publication interval outcome drift")
                disposition = case["resulting_disposition"]
                _require(disposition.get("head_state") == ("invalid" if entered else (
                    "unbound" if record_role == "R0" else "stale"
                )), f"{label} terminal disposition drift")
                bindings = _validate_embedded_runtime(case)
                _require(len(bindings) == 2, f"{label} process count drift")
                injected = [
                    event for event in case["domain_processes"][role]["runtime_trace"]
                    if event.get("stage_id") == stage and event.get("stage_edge") == "fault_injected"
                ]
                _require(len(injected) == 1, f"{label} exact injected edge drift")
    _require(number == 138, "materialization fault enumeration drift")


def _validate_observation_faults(value: Any) -> None:
    _require(value.get("fault_matrix_schema") == "CrossDomainOccupancyLiveObservationFaultAtomicity.v1",
             "observation fault schema drift")
    _require(
        value.get("case_count") == 36
        and value.get("stage_order") == list(OBSERVATION_STAGES)
        and value.get("context_order") == [row[0] for row in OBSERVATION_CONTEXTS]
        and value.get("edge") == "after",
        "OF001-OF036 matrix closure drift",
    )
    cases = value.get("cases")
    _require(isinstance(cases, list) and [row.get("case_id") for row in cases] == [f"OF{i:03d}" for i in range(1, 37)],
             "OF001-OF036 identity drift")
    number = 0
    for context, role, inspection_id, _record_role in OBSERVATION_CONTEXTS:
        for stage_index, stage in enumerate(OBSERVATION_STAGES):
            case = cases[number]
            number += 1
            label = case["case_id"]
            _require(
                case.get("context") == context and case.get("target_role") == role
                and case.get("inspection_id") == inspection_id
                and case.get("stage_id") == stage and case.get("edge") == "after",
                f"{label} cross-product coordinate drift",
            )
            _require(case.get("canonical_before") == case.get("canonical_after") == canonical_chain(),
                     f"{label} changed canonical authority")
            stage_code = stage.split("_", 1)[0] if stage_index >= 10 else stage
            expected_channel = "harness_private" if stage_index >= 10 else "original_stdin"
            _require(case.get("channel") == expected_channel
                     and case["failure"].get("stage_id") == stage_code
                     and case["failure"].get("reason_code") == f"injected_{stage_code}_after",
                     f"{label} rejection channel drift")
            _require(case["resulting_disposition"].get("head_state") == "invalid"
                     and case["resulting_disposition"].get("physical_current_head_guard_state") == "failed_closed",
                     f"{label} did not fail closed")
            if stage_index >= 10:
                _require(case.get("arm_invocation") is None and case.get("harness_trace"),
                         f"{label} harness-private fault boundary drift")
                _validate_harness_trace(case["harness_trace"])
            else:
                _require(case.get("arm_invocation") is not None and case.get("harness_trace") == [],
                         f"{label} process-side fault boundary drift")
                injected = [
                    event for event in case["domain_processes"][role]["runtime_trace"]
                    if event.get("stage_id") == stage and event.get("stage_edge") == "fault_injected"
                ]
                _require(len(injected) == 1, f"{label} exact injected edge drift")
            _require(len(_validate_embedded_runtime(case)) == 2,
                     f"{label} process count drift")
    _require(number == 36, "observation fault enumeration drift")


def _validate_liveness_adversaries(value: Any) -> None:
    _require(value.get("liveness_adversaries_schema") == "CrossDomainOccupancyLivenessAdversaries.v1",
             "liveness adversary schema drift")
    _require(value.get("case_count") == 6, "LV01-LV06 closure drift")
    cases = value.get("cases")
    _require(isinstance(cases, list) and [row.get("case_id") for row in cases] == [f"LV{i:02d}" for i in range(1, 7)],
             "LV01-LV06 identity drift")
    for case in cases:
        case_id = case["case_id"]
        role, checkpoint, channel, action, failure_code = LIVENESS_ROWS[case_id]
        _require(case.get("target_role", role) == role
                 and case.get("checkpoint_id") == checkpoint
                 and case.get("channel") == channel
                 and case.get("action_id") == action
                 and case.get("liveness_failure_code") == failure_code,
                 f"{case_id} liveness coordinate drift")
        _require(case.get("canonical_before") == case.get("canonical_after") == canonical_chain(),
                 f"{case_id} changed canonical authority")
        bindings = _validate_embedded_runtime(case)
        _require(len(bindings) == (3 if case_id == "LV06" else 2),
                 f"{case_id} process count drift")
        plan = case["liveness_plan"]
        _require(plan.get("case_id") == case_id and plan.get("domain_role") == role
                 and plan.get("checkpoint_id") == checkpoint and plan.get("channel") == channel
                 and plan.get("action_id") == action
                 and plan.get("terminal_liveness_failure_code") == failure_code,
                 f"{case_id} liveness plan drift")
        terminal = case["terminal_liveness_observation"]
        target_binding = case["domain_processes"][role]["binding"]
        _validate_liveness_observation(terminal, target_binding)
        _require(terminal.get("checkpoint_id") == "terminal_failure",
                 f"{case_id} terminal checkpoint drift")
        flags = {
            "LV01": terminal["original_child_handle_exit_observed"] is True and terminal["wait_status_available"] is False,
            "LV02": terminal["original_child_handle_exit_observed"] is True and terminal["wait_status_available"] is True,
            "LV03": terminal["process_start_pair_changed"] is False and case.get("liveness_adversarial_report") is not None,
            "LV04": terminal["control_pipe_unexpected_eof"] is True,
            "LV05": terminal["structured_output_pipe_unexpected_eof"] is True,
            "LV06": terminal["replacement_spawn_count"] == 1 and isinstance(case.get("replacement_process"), dict),
        }
        _require(flags[case_id], f"{case_id} terminal liveness witness drift")
        _require(all(row.get("head_state") == "protocol_invalid"
                     and row.get("reason_code") == "physical_protocol_violation"
                     for row in case["terminal_dispositions"].values()),
                 f"{case_id} terminal disposition drift")


def _validate_source_audit(value: Any, *, rerun: bool) -> None:
    _require(value.get("source_audit_schema") == "CrossDomainOccupancySourceAudit.v1",
             "source audit schema drift")
    _require(
        value.get("translation_unit_count") == 15
        and value.get("positive_check_count") == 30
        and value.get("mutation_count") == 18,
        "source audit count drift",
    )
    _require([row.get("path") for row in value["translation_units"]] == list(SOURCE_AUDIT_PATHS),
             "source audit translation-unit order drift")
    for row in value["translation_units"]:
        _require(_sha(ROOT / row["path"]) == row.get("raw_sha256"),
                 f"source audit byte drift: {row['path']}")
    _require([row.get("check_id") for row in value["source_checks"]] == list(SOURCE_CHECK_IDS)
             and all(row.get("result") == "PASS" for row in value["source_checks"]),
             "S01-S30 source check drift")
    _require([row.get("mutation_id") for row in value["mutations"]] == [row[0] for row in SOURCE_MUTATIONS]
             and all(row.get("result") == "REJECTED" for row in value["mutations"]),
             "18 source mutation rejection drift")
    if rerun:
        _require(acquire_source_audit() == value,
                 "independent source audit replay drift")


def _validate_input_audit(
    value: Any,
    primary: Mapping[str, Mapping[str, Any]],
    source_audit: Mapping[str, Any],
) -> None:
    _require(value.get("input_audit_schema") == "CrossDomainOccupancyProofSemanticInputAudit.v1",
             "semantic input audit schema drift")
    _require(value.get("process_count") == 8 and value.get("alternate_semantic_channel_count") == 0,
             "semantic input channel closure drift")
    _require(value.get("source_audit_raw_sha256") == sha256_value(source_audit),
             "semantic input source-audit relation drift")
    rows = value.get("process_rows")
    _require(isinstance(rows, list) and len(rows) == 8, "semantic input process registry drift")
    expected_pairs = [(witness, role) for witness in ("W1", "W2", "W3", "W4") for role in DOMAIN_ROLES]
    _require([(row.get("witness"), row.get("domain_role")) for row in rows] == expected_pairs,
             "semantic input process order drift")
    for row, (witness, role) in zip(rows, expected_pairs):
        process = primary[witness]["domain_processes"][role]
        provenance = process["runtime_provenance"]
        _require(row.get("binding") == process["binding"]
                 and row.get("launch_plan") == process["launch_plan"]
                 and row.get("bundle_inventory") == process["bundles"]
                 and row.get("command_rows") == process["commands"]
                 and row.get("loaded_image_inventory") == provenance["loaded_image_inventory"]
                 and row.get("initial_world_actor_class_inventory") == provenance["initial_world_actor_class_inventory"],
                 f"semantic input process relation drift: {witness}/{role}")


def _semantic_surface(witness: Mapping[str, Any]) -> Any:
    return semantic_replay_projection({
        "canonical_chain": witness["canonical_chain"],
        "dispositions": witness["dispositions"],
        "expectations": witness["expectations"],
        "observations": witness["observations"],
        "receipts": witness["receipts"],
        "refresh_orders": witness["refresh_orders"],
    })


def _validate_equivalence(value: Any, primary: Mapping[str, Mapping[str, Any]]) -> None:
    _require(value.get("canonical_equivalence_oracle_schema") == "CrossDomainOccupancyCanonicalEquivalenceOracle.v1",
             "canonical equivalence schema drift")
    _require(value.get("witness_count") == 4 and value.get("physical_input_to_scheduler_or_resolver") is False,
             "canonical equivalence authority drift")
    rows = value.get("witness_rows")
    _require(isinstance(rows, list) and [row.get("witness") for row in rows] == ["W1", "W2", "W3", "W4"],
             "canonical equivalence witness closure drift")
    for row in rows:
        witness = row["witness"]
        _require(primary[witness]["canonical_chain"] == canonical_chain()
                 and row.get("canonical_chain_raw_sha256") == sha256_value(primary[witness]["canonical_chain"])
                 and row.get("refresh_orders") == primary[witness]["refresh_orders"]
                 and row.get("rfinal_raw_sha256") == RAW_HASHES["Rfinal"],
                 f"canonical equivalence relation drift: {witness}")


def _validate_replay(value: Any, primary: Mapping[str, Mapping[str, Any]]) -> None:
    _require(value.get("replay_oracle_schema") == "CrossDomainOccupancyReplayOracle.v1"
             and value.get("repeat_count") == 4,
             "fresh replay oracle closure drift")
    repeats = value.get("repeats")
    _require(isinstance(repeats, list) and [row.get("witness") for row in repeats] == ["W1", "W2", "W3", "W4"],
             "fresh replay witness order drift")
    primary_ids = {
        operational_process_instance_id(process["binding"])
        for witness in primary.values() for process in witness["domain_processes"].values()
    }
    repeat_ids: set[str] = set()
    for repeat in repeats:
        witness_name = repeat["witness"]
        repeated = repeat["repeat_witness"]
        bindings = _validate_primary(repeated, witness_name)
        surface = _semantic_surface(repeated)
        primary_surface = _semantic_surface(primary[witness_name])
        _require(surface == primary_surface
                 and repeat.get("primary_semantic_raw_sha256") == sha256_value(primary_surface)
                 and repeat.get("repeat_semantic_raw_sha256") == sha256_value(surface),
                 f"{witness_name} fresh replay semantic drift")
        for identity in bindings:
            _require(identity not in primary_ids and identity not in repeat_ids,
                     f"{witness_name} replay process was not fresh")
            repeat_ids.add(identity)
    _require(len(repeat_ids) == 8, "fresh replay process closure drift")


def _occurrence_bindings(value: Mapping[str, Any], *, binding_case: bool = False) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    if binding_case:
        binding = value.get("nominal_binding")
        if isinstance(binding, dict):
            bindings.append(binding)
    else:
        processes = value.get("domain_processes")
        if isinstance(processes, dict):
            for process in processes.values():
                if isinstance(process, dict) and isinstance(process.get("binding"), dict):
                    bindings.append(process["binding"])
        replacement = value.get("replacement_process")
        if isinstance(replacement, dict):
            binding = replacement.get("nominal_binding", replacement.get("binding"))
            if isinstance(binding, dict):
                bindings.append(binding)
    unique: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        validated = _validated_binding(binding)
        unique[operational_process_instance_id(validated)] = validated
    return list(unique.values())


def _rebuilt_occurrence_row(
    occurrence_id: str,
    artifact_role: str,
    execution_mode: str,
    expected_process_count: int,
    value: Mapping[str, Any],
    *,
    binding_case: bool = False,
) -> dict[str, Any]:
    bindings = _occurrence_bindings(value, binding_case=binding_case)
    _require(len(bindings) == expected_process_count,
             f"{occurrence_id} occurrence process count drift")
    identities = [operational_process_instance_id(binding) for binding in bindings]
    births = [binding["macos_process_start"] for binding in bindings]
    roots = [binding["process_root_realpath"] for binding in bindings]
    _require(len(identities) == len(set(identities))
             and len(births) == len({canonical_json(row) for row in births})
             and len(roots) == len(set(roots)),
             f"{occurrence_id} occurrence process collision")
    trace_ranges: list[dict[str, Any]] = []
    stdin_ranges: list[dict[str, Any]] = []
    inventories: list[dict[str, Any]] = []
    processes = value.get("domain_processes", {})
    if isinstance(processes, dict):
        for role, process in processes.items():
            if not isinstance(process, dict):
                continue
            traces = process.get("runtime_trace") or []
            commands = process.get("commands") or []
            provenance = process.get("runtime_provenance") or {}
            trace_ranges.append({
                "domain_role": role,
                "event_count": len(traces),
                "first_sequence": None if not traces else traces[0]["trace_sequence"],
                "last_sequence": None if not traces else traces[-1]["trace_sequence"],
            })
            stdin_ranges.append({
                "command_count": len(commands),
                "domain_role": role,
                "first_command_sequence": None if not commands else commands[0].get("command_sequence"),
                "last_command_sequence": None if not commands else commands[-1].get("command_sequence"),
            })
            if provenance:
                inventories.append({
                    "domain_role": role,
                    "loaded_image_inventory_raw_sha256": sha256_value(provenance.get("loaded_image_inventory", [])),
                    "initial_actor_inventory_raw_sha256": sha256_value(provenance.get("initial_world_actor_class_inventory", [])),
                })
    harness_traces: list[Any] = []
    if isinstance(value.get("harness_trace"), list):
        harness_traces = value["harness_trace"]
    elif isinstance(value.get("fault"), dict):
        harness_traces = value["fault"].get("harness_trace", [])
    return {
        "actual_unique_process_count": len(bindings),
        "artifact_role": artifact_role,
        "execution_mode": execution_mode,
        "expected_process_count": expected_process_count,
        "harness_trace_range": {
            "event_count": len(harness_traces),
            "first_sequence": None if not harness_traces else harness_traces[0]["trace_sequence"],
            "last_sequence": None if not harness_traces else harness_traces[-1]["trace_sequence"],
        },
        "loaded_image_and_initial_actor_inventory_digests": inventories,
        "occurrence_id": occurrence_id,
        "operational_process_instance_ids": identities,
        "process_births": births,
        "process_roots": roots,
        "proof_scenario": PROOF_SCENARIO,
        "stdin_ranges": stdin_ranges,
        "terminal_disposition_raw_sha256": sha256_value(
            value.get("terminal_dispositions", value.get("resulting_disposition", {}))
        ),
        "trace_ranges": trace_ranges,
    }


def _rebuilt_registry(
    values: Mapping[str, Any], primary: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for witness in ("W1", "W2", "W3", "W4"):
        for role in DOMAIN_ROLES:
            rows.append(_rebuilt_occurrence_row(
                f"{witness}/{role}", f"physical_{witness}", "positive_primary_process", 1,
                {"domain_processes": {role: primary[witness]["domain_processes"][role]}},
            ))
    for case_id, filename in CONTROL_FILES.items():
        rows.append(_rebuilt_occurrence_row(
            case_id, f"control_{case_id}", "control", 3 if case_id == "C5" else 2,
            values[filename],
        ))
    for case_id, filename in ASYMMETRIC_FILES.items():
        rows.append(_rebuilt_occurrence_row(
            case_id, f"failure_{case_id}", "asymmetric_failure", 2, values[filename]
        ))
    binding = values["cross_domain_occupancy_process_binding_adversaries.json"]
    for case in binding["cases"]:
        rows.append(_rebuilt_occurrence_row(
            case["case_id"], "process_binding_adversaries", "binding_adversary", 1,
            case, binding_case=True,
        ))
    for filename, artifact_role, mode, count in (
        ("cross_domain_occupancy_head_publication_fault_atomicity.json", "head_publication_fault_atomicity", "head_fault", 2),
        ("cross_domain_occupancy_materialization_fault_atomicity.json", "materialization_fault_atomicity", "materialization_fault", 2),
        ("cross_domain_occupancy_live_observation_fault_atomicity.json", "live_observation_fault_atomicity", "observation_fault", 2),
    ):
        for case in values[filename]["cases"]:
            rows.append(_rebuilt_occurrence_row(
                case["case_id"], artifact_role, mode, count, case
            ))
    for case in values["cross_domain_occupancy_liveness_adversaries.json"]["cases"]:
        rows.append(_rebuilt_occurrence_row(
            case["case_id"], "liveness_adversaries", "liveness_adversary",
            3 if case["case_id"] == "LV06" else 2, case,
        ))
    authority = values["cross_domain_occupancy_authority_adversaries.json"]
    for case in authority["cases"]:
        for subcase in case["subcases"]:
            rows.append(_rebuilt_occurrence_row(
                subcase["subcase_id"], "authority_adversaries", "authority_subcase", 0, {}
            ))
    replay = values["cross_domain_occupancy_replay_oracle.json"]
    for repeat in replay["repeats"]:
        rows.append(_rebuilt_occurrence_row(
            f"replay/{repeat['witness']}", "replay_oracle", "replay_repeat", 2,
            repeat["repeat_witness"],
        ))
    identities = [identity for row in rows for identity in row["operational_process_instance_ids"]]
    _require(len(rows) == 364 and len(identities) == len(set(identities)) == 457,
             "364-occurrence / 457-process registry closure drift")
    return {
        "occurrence_count": 364,
        "process_occurrence_registry_schema": "CrossDomainOccupancyProcessOccurrenceRegistry.v1",
        "proof_scenario": PROOF_SCENARIO,
        "registered_unique_process_count": 457,
        "result": "PASS",
        "rows": rows,
    }


def _validate_registry(
    value: Any, values: Mapping[str, Any], primary: Mapping[str, Mapping[str, Any]],
) -> None:
    _require(value == _rebuilt_registry(values, primary),
             "process occurrence registry relation drift")


def _rebuilt_proof_run(values: Mapping[str, Any]) -> dict[str, Any]:
    payloads = {
        name: value for name, value in values.items()
        if name != "cross_domain_occupancy_proof_run.json"
    }
    _require(set(payloads) == set(ARTIFACT_NAMES) - {"cross_domain_occupancy_proof_run.json"},
             "81-member proof payload closure drift")
    return {
        "UE_5_8_build_required": True,
        "artifact_member_count": 82,
        "artifact_payload_raw_sha256": {
            name: sha256_value(value) for name, value in sorted(payloads.items())
        },
        "asymmetric_failure_count": 4,
        "authority_case_count": 40,
        "authority_subcase_count": 121,
        "capacity_advancement": "none",
        "control_count": 6,
        "evidence_status": "unsealed",
        "focused_test_contract_count": 45,
        "head_publication_fault_count": 18,
        "liveness_adversary_count": 6,
        "live_observation_fault_count": 36,
        "manifest_self_excluding": True,
        "materialization_fault_count": 138,
        "phase_5_state": "closed",
        "primary_witness_count": 4,
        "process_binding_adversary_count": 23,
        "process_occurrence_count": 364,
        "proof_scenario": PROOF_SCENARIO,
        "proof_schema": "CrossDomainOccupancyProofRun.v1",
        "proof_version": PROOF_VERSION,
        "release_member_count": 172,
        "replay_repeat_count": 4,
        "result": "PASS",
        "source_check_count": 30,
        "source_mutation_rejection_count": 18,
    }


def _validate_proof_run(value: Any, values: Mapping[str, Any]) -> None:
    rebuilt_values = dict(values)
    rebuilt_values["cross_domain_occupancy_proof_run.json"] = value
    _require(value == _rebuilt_proof_run(rebuilt_values), "proof-run relation drift")


def _load_artifacts(directory: Path) -> dict[str, Any]:
    _require(directory.is_dir() and not directory.is_symlink(),
             "artifact directory absent or linked")
    try:
        directory.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
    except ValueError as exc:
        raise ValueError("artifact directory escapes repository") from exc
    _require(artifact_role_set_valid(directory), "exact 82-member artifact role set drift")
    values: dict[str, Any] = {}
    for name in ARTIFACT_NAMES:
        path = directory / name
        _regular_member(path, directory)
        values[name] = strict_load_stored_json(path.read_bytes())
    return values


def validate_artifact_semantics(
    directory: Path, *, rerun_source_audit: bool = True,
) -> dict[str, Any]:
    values = _load_artifacts(directory)
    _require(values["cross_domain_occupancy_canonical_chain.json"] == canonical_chain(),
             "canonical-chain artifact drift")
    _require(values["cross_domain_occupancy_projection_matrix.json"] == projection_matrix(),
             "projection-matrix artifact drift")
    _require(values["cross_domain_occupancy_operation_tuple_matrix.json"] == operation_tuple_matrix(),
             "operation-tuple artifact drift")
    _require(
        values["cross_domain_occupancy_guard_and_head_observation_matrix.json"]
        == guard_and_head_observation_matrix(),
        "guard/head-observation matrix drift",
    )
    primary: dict[str, Mapping[str, Any]] = {}
    all_process_ids: set[str] = set()
    for witness, filename in PRIMARY_FILES.items():
        primary[witness] = values[filename]
        bindings = _validate_primary(values[filename], witness, values)
        for identity in bindings:
            _require(identity not in all_process_ids, "primary process reused across witnesses")
            all_process_ids.add(identity)
    _require(len(all_process_ids) == 8, "eight fresh primary process closure drift")
    _validate_controls(values)
    _validate_asymmetric(values)
    _validate_binding_adversaries(values["cross_domain_occupancy_process_binding_adversaries.json"])
    _validate_authority_adversaries(values["cross_domain_occupancy_authority_adversaries.json"])
    _validate_head_faults(values["cross_domain_occupancy_head_publication_fault_atomicity.json"])
    _validate_materialization_faults(values["cross_domain_occupancy_materialization_fault_atomicity.json"])
    _validate_observation_faults(values["cross_domain_occupancy_live_observation_fault_atomicity.json"])
    _validate_liveness_adversaries(values["cross_domain_occupancy_liveness_adversaries.json"])
    source = values["cross_domain_occupancy_source_audit.json"]
    _validate_source_audit(source, rerun=rerun_source_audit)
    _validate_input_audit(
        values["cross_domain_occupancy_proof_semantic_input_audit.json"], primary, source
    )
    _validate_equivalence(
        values["cross_domain_occupancy_canonical_equivalence_oracle.json"], primary
    )
    _validate_replay(values["cross_domain_occupancy_replay_oracle.json"], primary)
    _validate_registry(
        values["cross_domain_occupancy_process_occurrence_registry.json"], values, primary
    )
    _validate_proof_run(values["cross_domain_occupancy_proof_run.json"], values)
    for name, value in values.items():
        if isinstance(value, dict) and "proof_scenario" in value:
            _require(value["proof_scenario"] == PROOF_SCENARIO,
                     f"{name} proof-scenario drift")
        if isinstance(value, dict) and "result" in value:
            _require(value["result"] == "PASS", f"{name} result drift")
    return values


def _rebuilt_artifacts(values: Mapping[str, Any]) -> dict[str, Any]:
    rebuilt: dict[str, Any] = {
        "cross_domain_occupancy_canonical_chain.json": canonical_chain(),
        "cross_domain_occupancy_projection_matrix.json": projection_matrix(),
        "cross_domain_occupancy_operation_tuple_matrix.json": operation_tuple_matrix(),
        "cross_domain_occupancy_guard_and_head_observation_matrix.json": guard_and_head_observation_matrix(),
    }
    for witness, filename in PRIMARY_FILES.items():
        value = values[filename]
        for record_role in RECORD_ROLES:
            for role in DOMAIN_ROLES:
                letter = role[-1]
                rebuilt[f"physical_{witness}_domain_{letter}_{record_role}_materialization_receipt.json"] = value["receipts"][role][record_role]
                rebuilt[f"physical_{witness}_domain_{letter}_{record_role}_live_observation.json"] = value["observations"][role][record_role]
        rebuilt[f"physical_{witness}_liveness_witness.json"] = {
            "checkpoints": value["checkpoints"],
            "proof_scenario": PROOF_SCENARIO,
            "result": "PASS",
            "terminations": value["terminations"],
            "witness_id": value["witness_id"],
        }
        rebuilt[filename] = value
    for filename in CONTROL_FILES.values():
        rebuilt[filename] = values[filename]
    for filename in ASYMMETRIC_FILES.values():
        rebuilt[filename] = values[filename]
    aggregate_names = (
        "cross_domain_occupancy_process_binding_adversaries.json",
        "cross_domain_occupancy_authority_adversaries.json",
        "cross_domain_occupancy_head_publication_fault_atomicity.json",
        "cross_domain_occupancy_materialization_fault_atomicity.json",
        "cross_domain_occupancy_live_observation_fault_atomicity.json",
        "cross_domain_occupancy_liveness_adversaries.json",
        "cross_domain_occupancy_proof_semantic_input_audit.json",
        "cross_domain_occupancy_canonical_equivalence_oracle.json",
        "cross_domain_occupancy_source_audit.json",
        "cross_domain_occupancy_replay_oracle.json",
    )
    for name in aggregate_names:
        rebuilt[name] = values[name]
    primary = {witness: values[filename] for witness, filename in PRIMARY_FILES.items()}
    rebuilt["cross_domain_occupancy_process_occurrence_registry.json"] = _rebuilt_registry(rebuilt | values, primary)
    rebuilt["cross_domain_occupancy_proof_run.json"] = _rebuilt_proof_run(rebuilt)
    _require(set(rebuilt) == set(ARTIFACT_NAMES), "isolated 82-member reconstruction drift")
    return rebuilt


def _isolated_regeneration(directory: Path, values: Mapping[str, Any]) -> None:
    rebuilt = _rebuilt_artifacts(values)
    with tempfile.TemporaryDirectory(prefix="thecity-phase4-regeneration-", dir="/private/tmp") as temporary:
        destination = Path(temporary) / "artifacts"
        destination.mkdir()
        for name in ARTIFACT_NAMES:
            write_json(destination / name, rebuilt[name])
        _require(artifact_role_set_valid(destination), "isolated artifact role regeneration drift")
        for name in ARTIFACT_NAMES:
            _require((destination / name).read_bytes() == (directory / name).read_bytes(),
                     f"isolated artifact regeneration mismatch: {name}")


def _run_negative_tests(values: Mapping[str, Any]) -> int:
    primary = {witness: values[filename] for witness, filename in PRIMARY_FILES.items()}
    rejected = 0

    def reject(
        label: str, source: Any, mutation: Callable[[Any], None], validator: Callable[[Any], None],
    ) -> None:
        nonlocal rejected
        payload = copy.deepcopy(source)
        mutation(payload)
        try:
            validator(payload)
        except Exception:
            rejected += 1
            return
        raise ValueError(f"verifier mutation was accepted: {label}")

    reject("canonical_chain", values["cross_domain_occupancy_canonical_chain.json"],
           lambda row: row.__setitem__("proof_scenario", "mutated"),
           lambda row: _require(row == canonical_chain(), "mutated canonical chain"))
    reject("projection_matrix", values["cross_domain_occupancy_projection_matrix.json"],
           lambda row: row["rows"].pop(),
           lambda row: _require(row == projection_matrix(), "mutated projection matrix"))
    reject("operation_matrix", values["cross_domain_occupancy_operation_tuple_matrix.json"],
           lambda row: row["rows"][0].__setitem__("domain_role", "domain_Z"),
           lambda row: _require(row == operation_tuple_matrix(), "mutated operation matrix"))
    reject("guard_matrix", values["cross_domain_occupancy_guard_and_head_observation_matrix.json"],
           lambda row: row["permission_rows"].pop(),
           lambda row: _require(row == guard_and_head_observation_matrix(), "mutated guard matrix"))
    reject("primary_refresh_order", primary["W1"],
           lambda row: row["refresh_orders"]["Rtransit"].reverse(),
           lambda row: _validate_primary(row, "W1"))
    reject("primary_receipt", primary["W1"],
           lambda row: row["receipts"]["domain_A"]["R0"].__setitem__("accepted_canonical_hash", "0" * 64),
           lambda row: _validate_primary(row, "W1"))
    reject("primary_observation", primary["W1"],
           lambda row: row["observations"]["domain_B"]["R0"].__setitem__("subject_actor_count", 0),
           lambda row: _validate_primary(row, "W1"))
    reject("primary_binding", primary["W1"],
           lambda row: row["domain_processes"]["domain_A"]["binding"].__setitem__("pid", -1),
           lambda row: _validate_primary(row, "W1"))
    reject("primary_trace", primary["W1"],
           lambda row: row["domain_processes"]["domain_A"]["runtime_trace"][0].__setitem__("trace_sequence", 9),
           lambda row: _validate_primary(row, "W1"))
    reject("primary_checkpoint", primary["W1"],
           lambda row: row["checkpoints"][0].__setitem__("checkpoint_id", "LX"),
           lambda row: _validate_primary(row, "W1"))

    controls = {name: values[name] for name in CONTROL_FILES.values()}
    reject("control_identity", controls,
           lambda row: row[CONTROL_FILES["C1"]].__setitem__("case_id", "CX"), _validate_controls)
    reject("control_failure", controls,
           lambda row: row[CONTROL_FILES["C3"]]["failure"].__setitem__("stage_id", "M00"), _validate_controls)
    reject("control_replacement", controls,
           lambda row: row[CONTROL_FILES["C5"]].__setitem__("replacement_rejected_as_continuity", False), _validate_controls)

    asymmetric = {name: values[name] for name in ASYMMETRIC_FILES.values()}
    reject("asymmetric_role", asymmetric,
           lambda row: row[ASYMMETRIC_FILES["AF01"]].__setitem__("failed_role", "domain_A"), _validate_asymmetric)
    reject("asymmetric_digest", asymmetric,
           lambda row: row[ASYMMETRIC_FILES["AF02"]]["failed_bundle"].__setitem__("malformed_projection_raw_sha256", "0" * 64), _validate_asymmetric)

    binding = values["cross_domain_occupancy_process_binding_adversaries.json"]
    reject("binding_count", binding, lambda row: row.__setitem__("case_count", 22), _validate_binding_adversaries)
    reject("binding_field", binding, lambda row: row["cases"][0].__setitem__("changed_fields", []), _validate_binding_adversaries)

    authority = values["cross_domain_occupancy_authority_adversaries.json"]
    reject("authority_count", authority, lambda row: row.__setitem__("subcase_count", 120), _validate_authority_adversaries)
    reject("authority_reason", authority,
           lambda row: row["cases"][0]["subcases"][0].__setitem__("actual_rejection_reason", "accepted"),
           _validate_authority_adversaries)

    head_faults = values["cross_domain_occupancy_head_publication_fault_atomicity.json"]
    reject("head_fault_count", head_faults, lambda row: row.__setitem__("case_count", 17), _validate_head_faults)
    reject("head_fault_trace", head_faults,
           lambda row: row["cases"][0]["fault"]["harness_trace"].pop(), _validate_head_faults)

    materialization = values["cross_domain_occupancy_materialization_fault_atomicity.json"]
    reject("materialization_count", materialization, lambda row: row.__setitem__("case_count", 137), _validate_materialization_faults)
    reject("materialization_edge", materialization,
           lambda row: row["cases"][0].__setitem__("edge", "invalid"), _validate_materialization_faults)

    observations = values["cross_domain_occupancy_live_observation_fault_atomicity.json"]
    reject("observation_count", observations, lambda row: row.__setitem__("case_count", 35), _validate_observation_faults)
    reject("observation_channel", observations,
           lambda row: row["cases"][0].__setitem__("channel", "alternate"), _validate_observation_faults)

    liveness = values["cross_domain_occupancy_liveness_adversaries.json"]
    reject("liveness_failure", liveness,
           lambda row: row["cases"][0].__setitem__("liveness_failure_code", "accepted"), _validate_liveness_adversaries)

    source = values["cross_domain_occupancy_source_audit.json"]
    reject("source_check", source,
           lambda row: row["source_checks"][0].__setitem__("result", "ACCEPTED"),
           lambda row: _validate_source_audit(row, rerun=False))
    replay = values["cross_domain_occupancy_replay_oracle.json"]
    reject("replay_digest", replay,
           lambda row: row["repeats"][0].__setitem__("repeat_semantic_raw_sha256", "0" * 64),
           lambda row: _validate_replay(row, primary))
    registry = values["cross_domain_occupancy_process_occurrence_registry.json"]
    reject("registry_count", registry, lambda row: row.__setitem__("occurrence_count", 363),
           lambda row: _validate_registry(row, values | {"cross_domain_occupancy_process_occurrence_registry.json": row}, primary))
    proof_run = values["cross_domain_occupancy_proof_run.json"]
    reject("proof_run_digest", proof_run,
           lambda row: row["artifact_payload_raw_sha256"].__setitem__(next(iter(row["artifact_payload_raw_sha256"])), "0" * 64),
           lambda row: _validate_proof_run(row, values | {"cross_domain_occupancy_proof_run.json": row}))
    _require(rejected == 30, "30-mutation verifier closure drift")
    return rejected


def _run_test_contracts() -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPYCACHEPREFIX"] = "/private/tmp/thecity_phase4_verifier_pycache"
    focused = subprocess.run(
        [sys.executable, "-m", "unittest", "test_cross_domain_canonical_occupancy_materialization.py"],
        cwd=ROOT / "proof_kernel", env=environment, capture_output=True, text=True,
    )
    focused_output = focused.stdout + focused.stderr
    _require(focused.returncode == 0 and "Ran 45 tests" in focused_output and "OK" in focused_output,
             f"focused Phase-4 tests failed:\n{focused_output}")
    predecessor_files = sorted(
        path.name for path in (ROOT / "proof_kernel").glob("test_*.py")
        if path.name not in {
            "test_cross_domain_canonical_occupancy_materialization.py",
            "test_simultaneous_physical_domains.py",
        }
    )
    predecessor = subprocess.run(
        [sys.executable, "-m", "unittest", *predecessor_files],
        cwd=ROOT / "proof_kernel", env=environment, capture_output=True, text=True,
    )
    predecessor_output = predecessor.stdout + predecessor.stderr
    _require(predecessor.returncode == 0 and "Ran 215 tests" in predecessor_output and "OK" in predecessor_output,
             f"215 predecessor regressions failed:\n{predecessor_output}")


def verify_artifacts() -> int:
    directory = ROOT / ARTIFACT_DIRECTORY
    values = validate_artifact_semantics(directory, rerun_source_audit=True)
    _isolated_regeneration(directory, values)
    rejected = _run_negative_tests(values)
    _run_test_contracts()
    return rejected


def _validate_unchanged_members() -> None:
    for relative, expected_digest in UNCHANGED_NON_ARTIFACT_SHA256.items():
        _require(_sha(_regular_release_member(relative)) == expected_digest,
                 f"frozen unchanged member drift: {relative}")


def _parse_manifest() -> list[tuple[str, str]]:
    path = ROOT / MANIFEST
    _regular_member(path, ROOT)
    raw = path.read_bytes()
    _require(raw.endswith(b"\n") and b"\r" not in raw, "manifest encoding drift")
    parsed: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in raw.decode("utf-8", errors="strict").splitlines():
        digest, separator, relative = line.partition("  ")
        candidate = Path(relative)
        _require(
            separator == "  " and is_sha256(digest) and relative and relative not in seen
            and relative != MANIFEST and not candidate.is_absolute() and ".." not in candidate.parts,
            f"invalid manifest line: {line!r}",
        )
        seen.add(relative)
        parsed.append((digest, relative))
    _require(tuple(relative for _, relative in parsed) == release_paths(),
             "manifest exact order/member closure drift")
    return parsed


def write_release() -> int:
    _require((ROOT / EVIDENCE_DOCUMENT).is_file(), "evidence document is required")
    verify_artifacts()
    _validate_unchanged_members()
    members = release_paths()
    for relative in members:
        _regular_release_member(relative)
    (ROOT / MANIFEST).write_text(
        "".join(f"{_sha(ROOT / relative)}  {relative}\n" for relative in members),
        encoding="utf-8",
    )
    return len(members)


def verify_release() -> int:
    _require((ROOT / EVIDENCE_DOCUMENT).is_file(), "evidence document is required")
    parsed = _parse_manifest()
    _validate_unchanged_members()
    for digest, relative in parsed:
        _require(_sha(_regular_release_member(relative)) == digest,
                 f"manifest checksum mismatch: {relative}")
    verify_artifacts()
    return len(parsed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("artifacts", "write-release", "verify"))
    arguments = parser.parse_args()
    if arguments.command == "artifacts":
        rejected = verify_artifacts()
        print(
            f"verified exact 82/82 Phase-4 artifacts; verifier adversaries {rejected}/{rejected} rejected; "
            "evidence remains unsealed"
        )
        return 0
    count = write_release() if arguments.command == "write-release" else verify_release()
    print(
        f"verified {count}/{count} release members; verifier adversaries 30/30 rejected; "
        "manifest excludes itself; evidence remains unsealed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
