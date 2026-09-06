# Git history and LFS transport

The Phase-4 materialization-fault evidence is stored through Git LFS. Its two historical payloads exceeded GitHub's regular Git file limit. The conversion affects only the six commits after `81b1cc9b37003476f31148f6e456cab669925ab9`.

All original checked-out source, document, manifest, and evidence bytes are preserved. `.gitattributes` declares the single LFS path. The converted commits have new Git identities, recorded in `LFS-commit-map.csv`. This storage conversion grants no new proof seal, capacity, or implementation authority.

## Original sealed history

`THE_CITY-pre-LFS.bundle` contains the complete original committed history. It preserves these exact identities:

- Original HEAD: `ef778721be24b8b47f709604d957f5635f358b02`
- Original HEAD tree: `3eac79ef39dd01392e22ca1987daf7b918c64385`
- Accepted Phase-4 candidate: `bee3ecca660f884f3af727affae3ab1ceae2c401`
- Original Phase-4 seal: `5d4eac983de281fcf7b03d78453e5f131204b946`
- Bundle SHA-256: `5dc6076cdcfeb880872e15adaca880b0f20255e28d1312b1597faac666ea1f0e`

Historical seal claims refer to those original objects. The conversion map does not substitute new commit identities for the old review or seal decisions. Untracked reference documents are outside this committed-history archive.

Verify the archive from the repository root:

```sh
git bundle verify "References/Git History/THE_CITY-pre-LFS.bundle"
shasum -a 256 "References/Git History/THE_CITY-pre-LFS.bundle"
```

Restore the original repository into a fresh destination for exact-commit audits:

```sh
git clone "References/Git History/THE_CITY-pre-LFS.bundle" /private/tmp/THE_CITY-original-seal-review
```

Use a fresh destination path if that example already exists. The restored repository contains the original full Git blobs and needs no LFS hydration for its historical release checks.

## Current checkout

Git LFS must supply the complete evidence file before release verification:

```sh
git lfs pull
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=proof_kernel \
  python3 proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py verify
```

A plain `git archive` of the converted branch contains an LFS pointer for the converted file. Run current release verification on a hydrated checkout. Run exact original-commit audits from the archived history above.

The converted checkout passed the 172-member release verifier, its 34 negative checks, 45 focused tests, and 215 predecessor regressions. No Unreal rebuild or new live-process acquisition was performed for this transport conversion.
