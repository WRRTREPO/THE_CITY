#include "CrossDomainOccupancyProofAdapter.h"

#include "CrossDomainOccupancyHeadAnchorActor.h"
#include "CrossDomainOccupancySubjectActor.h"
#include "Dom/JsonObject.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "Misc/Paths.h"
#include "Misc/ScopeExit.h"

#include <dirent.h>
#include <fcntl.h>
#include <limits.h>
#include <sys/stat.h>
#include <unistd.h>

namespace
{
using namespace CrossDomainOccupancyJson;

constexpr TCHAR Scenario[] = TEXT("cross-domain-canonical-occupancy-materialization-v1");
constexpr TCHAR Occupant[] = TEXT("topology_occupant_0001");
constexpr TCHAR Transition[] = TEXT("occupancy_transition_0001");
constexpr TCHAR SiteA[] = TEXT("topology_site_0001");
constexpr TCHAR SiteB[] = TEXT("topology_site_0002");
constexpr TCHAR H0[] = TEXT("b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8");
constexpr TCHAR HTransit[] = TEXT("2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19");
constexpr TCHAR HFinal[] = TEXT("3a00d32115af74950923ac3362a8459d0e08043d45abbe91bcc573e27103db34");
constexpr TCHAR D0[] = TEXT("59ce47bc4d6c63cbda4a740fec8d25e497ca8ed74052b16b5358745be115c2dc");
constexpr TCHAR DTransit[] = TEXT("215e3383bff21a9fe01dbb240035a0fa5dd774c703417486846e027a0615a12f");
constexpr TCHAR DFinal[] = TEXT("0b4d9d97eb166b3aae6480c5581654c39b367c3a5fab47a02daec50b1e88a181");

struct FOperationRow
{
    FString Operation;
    FString RelativeRoot;
    FString PayloadName;
    FString ProjectionName;
    FString InvocationName;
    FString SourceHash;
    FString TargetHash;
    FString PayloadDigest;
    FString ProjectionDigest;
    FString ProjectionId;
    FString Generation;
};

bool OperationRow(const FString& Role, const FString& OperationId, FOperationRow& Out)
{
    const bool bA = Role == TEXT("domain_A");
    const bool bB = Role == TEXT("domain_B");
    if (!bA && !bB) return false;
    const FString Letter = bA ? TEXT("A") : TEXT("B");
    if (OperationId == TEXT("launch_0001"))
    {
        Out = {
            TEXT("materialize_initial"), TEXT("launch_input/launch_0001"),
            TEXT("canonical_occupancy_R0.json"),
            FString::Printf(TEXT("cross_domain_%s_R0_projection.json"), *Letter),
            FString::Printf(TEXT("cross_domain_%s_launch_R0_invocation.json"), *Letter),
            TEXT(""), H0, D0,
            bA ? TEXT("c175ee92a3c69adbbeebaeecdabb54e462bbea1aa99f43117c5205757bcc9624")
               : TEXT("4d8da172945e1ff97433fe6230290f448d8731ac0dd5d3cef421e806b43531cb"),
            FString::Printf(TEXT("cross_domain_%s_R0_0001"), *Letter), TEXT("publication_0001")
        };
        return true;
    }
    if (OperationId == TEXT("refresh_0001"))
    {
        Out = {
            TEXT("refresh_once"), TEXT("refresh_input/refresh_0001"),
            TEXT("canonical_occupancy_Rtransit.json"),
            FString::Printf(TEXT("cross_domain_%s_Rtransit_projection.json"), *Letter),
            FString::Printf(TEXT("cross_domain_%s_refresh_Rtransit_invocation.json"), *Letter),
            H0, HTransit, DTransit,
            bA ? TEXT("1f57d0fc964956275008fffeb82adbb365f7c3343cce76d90e5cbd53262d68e6")
               : TEXT("1e72049befcbd9d1af6babaf855440c14101faa2d4aa5b97d13b9ae859d8d5dc"),
            FString::Printf(TEXT("cross_domain_%s_Rtransit_0001"), *Letter), TEXT("publication_0002")
        };
        return true;
    }
    if (OperationId == TEXT("refresh_0002"))
    {
        Out = {
            TEXT("refresh_once"), TEXT("refresh_input/refresh_0002"),
            TEXT("canonical_occupancy_Rfinal.json"),
            FString::Printf(TEXT("cross_domain_%s_Rfinal_projection.json"), *Letter),
            FString::Printf(TEXT("cross_domain_%s_refresh_Rfinal_invocation.json"), *Letter),
            HTransit, HFinal, DFinal,
            bA ? TEXT("723d9e539f3e0cebdab418dfacb25f8f2d6bbc0acd42c85a5330dca322a5e6c8")
               : TEXT("1552fb88285ffe670f1866ac324ef4b61c51d4ec2c4977df84e23b97e8eb85b9"),
            FString::Printf(TEXT("cross_domain_%s_Rfinal_0001"), *Letter), TEXT("publication_0003")
        };
        return true;
    }
    return false;
}

bool StoredObject(const TArray<uint8>& Bytes, TSharedPtr<FJsonObject>& Out)
{
    if (Bytes.Num() < 3 || Bytes.Last() != '\n') return false;
    int32 Newlines = 0;
    for (const uint8 Byte : Bytes)
    {
        if (Byte == '\r') return false;
        if (Byte == '\n') ++Newlines;
    }
    if (Newlines != 1) return false;
    FUTF8ToTCHAR Converted(reinterpret_cast<const ANSICHAR*>(Bytes.GetData()), Bytes.Num() - 1);
    return ParseCanonicalObject(FString(Converted.Length(), Converted.Get()), Out);
}

bool IsNullField(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field)
{
    const TSharedPtr<FJsonValue>* Value = Object.IsValid() ? Object->Values.Find(Field) : nullptr;
    return Value != nullptr && Value->IsValid() && (*Value)->IsNull();
}

TSharedPtr<FJsonValue> ObjectValue(const TSharedPtr<FJsonObject>& Object)
{
    return MakeShared<FJsonValueObject>(Object);
}

TSharedPtr<FJsonObject> FileWitnessRow(const FCDOInputFileWitness& File)
{
    TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
    Row->SetStringField(TEXT("device"), FString::Printf(TEXT("%llu"), static_cast<unsigned long long>(File.Device)));
    Row->SetStringField(TEXT("filename"), File.Filename);
    Row->SetStringField(TEXT("inode"), FString::Printf(TEXT("%llu"), static_cast<unsigned long long>(File.Inode)));
    Row->SetStringField(TEXT("raw_sha256"), File.RawSha256);
    Row->SetStringField(TEXT("realpath"), File.Realpath);
    Row->SetNumberField(TEXT("size"), File.Size);
    return Row;
}

TSharedPtr<FJsonObject> PrivateAnchorRow(const FCDOCandidateValues& Candidate, const FCDOImmutableProcessBinding& Binding)
{
    TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
    Row->SetStringField(TEXT("accepted_canonical_hash"), Candidate.CanonicalHash);
    Row->SetStringField(TEXT("accepted_canonical_payload_raw_sha256"), Candidate.CanonicalPayloadRawSha256);
    Row->SetStringField(TEXT("accepted_projection_id"), Candidate.ProjectionId);
    Row->SetStringField(TEXT("accepted_projection_raw_sha256"), Candidate.ProjectionRawSha256);
    Row->SetStringField(TEXT("actor_class"), TEXT("/Script/CityMaterializationProof.CrossDomainOccupancyHeadAnchorActor"));
    Row->SetStringField(TEXT("actor_path"), TEXT("private_candidate/head_anchor"));
    Row->SetStringField(TEXT("anchor_schema"), TEXT("CrossDomainOccupancyHeadAnchor.v1"));
    Row->SetStringField(TEXT("canonical_occupancy_kind"), Candidate.OccupancyKind);
    Row->SetStringField(TEXT("canonical_occupancy_reference"), Candidate.OccupancyReference);
    Row->SetStringField(TEXT("canonical_occupant_id"), Occupant);
    Row->SetStringField(TEXT("domain_role"), Candidate.DomainRole);
    Row->SetStringField(TEXT("local_subject_disposition"), Candidate.LocalDisposition);
    Row->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    Row->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
    Row->SetStringField(TEXT("projected_canonical_site_id"), Candidate.ProjectedSiteId);
    Row->SetStringField(TEXT("projected_site_representation_slot"), Candidate.SiteSlot);
    Row->SetStringField(TEXT("projected_subject_representation_slot"), Candidate.SubjectSlot);
    Row->SetStringField(TEXT("proof_scenario"), Scenario);
    Row->SetStringField(TEXT("publication_generation"), Candidate.PublicationGeneration);
    Row->SetStringField(TEXT("representation_publication_state"), TEXT("locally_published_unverified"));
    return Row;
}

TSharedPtr<FJsonObject> PrivateSubjectRow(const FCDOCandidateValues& Candidate, const FCDOImmutableProcessBinding& Binding)
{
    TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
    Row->SetStringField(TEXT("accepted_canonical_hash"), Candidate.CanonicalHash);
    Row->SetStringField(TEXT("accepted_canonical_payload_raw_sha256"), Candidate.CanonicalPayloadRawSha256);
    Row->SetStringField(TEXT("accepted_projection_id"), Candidate.ProjectionId);
    Row->SetStringField(TEXT("accepted_projection_raw_sha256"), Candidate.ProjectionRawSha256);
    Row->SetStringField(TEXT("actor_class"), TEXT("/Script/CityMaterializationProof.CrossDomainOccupancySubjectActor"));
    Row->SetStringField(TEXT("actor_path"), TEXT("private_candidate/subject"));
    Row->SetStringField(TEXT("canonical_occupant_id"), Occupant);
    Row->SetStringField(TEXT("domain_role"), Candidate.DomainRole);
    Row->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    Row->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
    Row->SetStringField(TEXT("proof_scenario"), Scenario);
    Row->SetStringField(TEXT("publication_generation"), Candidate.PublicationGeneration);
    Row->SetStringField(TEXT("representation_publication_state"), TEXT("locally_published_unverified"));
    Row->SetStringField(TEXT("represented_site_id"), Candidate.ProjectedSiteId);
    Row->SetStringField(TEXT("subject_representation_slot"), Candidate.SubjectSlot);
    Row->SetStringField(TEXT("subject_schema"), TEXT("CrossDomainOccupancySubjectRepresentation.v1"));
    return Row;
}
}

FCrossDomainOccupancyProofAdapter::FCrossDomainOccupancyProofAdapter(
    UWorld* InWorld,
    const FCDOImmutableProcessBinding& InBinding)
    : World(InWorld), Binding(InBinding)
{
}

bool FCrossDomainOccupancyProofAdapter::Stage(
    const FString& StageId,
    FCDOInjectedFaultPlan* FaultPlan,
    const TFunction<bool()>& Work,
    FString& OutReason,
    const TArray<TSharedPtr<FJsonValue>>& InputRows,
    const TSharedPtr<FJsonObject>& OutputIdentity) const
{
    CrossDomainOccupancyRuntime::EmitStage(
        StageId, TEXT("entered"), PublicationGeneration, RepresentedCanonicalHash, InputRows);
    if (CrossDomainOccupancyRuntime::InjectAt(FaultPlan, StageId, TEXT("before"), OutReason)) return false;
    if (!Work())
    {
        if (OutReason.IsEmpty()) OutReason = StageId + TEXT("_failed");
        return false;
    }
    CrossDomainOccupancyRuntime::EmitStage(
        StageId, TEXT("completed"), PublicationGeneration, RepresentedCanonicalHash, InputRows, OutputIdentity);
    if (CrossDomainOccupancyRuntime::InjectAt(FaultPlan, StageId, TEXT("after"), OutReason)) return false;
    return true;
}

bool FCrossDomainOccupancyProofAdapter::InventoryBundle(
    const FString& OperationId,
    const FString& RelativeBundleRoot,
    int& OutDirectoryDescriptor,
    TArray<FCDOInputFileWitness>& OutFiles,
    FString& OutReason) const
{
    FOperationRow Row;
    if (!OperationRow(Binding.DomainRole, OperationId, Row) || RelativeBundleRoot != Row.RelativeRoot ||
        RelativeBundleRoot.StartsWith(TEXT("/")) || RelativeBundleRoot.Contains(TEXT("..")))
    {
        OutReason = TEXT("operation_tuple_or_relative_root_mismatch");
        return false;
    }
    const FString Root = FPaths::Combine(Binding.ProcessRootRealpath, RelativeBundleRoot);
    FTCHARToUTF8 RootUtf8(*Root);
    char Resolved[PATH_MAX] {};
    if (realpath(RootUtf8.Get(), Resolved) == nullptr)
    {
        OutReason = TEXT("bundle_realpath_resolution_failed");
        return false;
    }
    const FString RootRealpath(UTF8_TO_TCHAR(Resolved));
    if (!RootRealpath.StartsWith(Binding.ProcessRootRealpath + TEXT("/")))
    {
        OutReason = TEXT("bundle_root_escape");
        return false;
    }
    OutDirectoryDescriptor = open(Resolved, O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    if (OutDirectoryDescriptor < 0)
    {
        OutReason = TEXT("bundle_directory_open_failed");
        return false;
    }

    DIR* Directory = fdopendir(dup(OutDirectoryDescriptor));
    if (Directory == nullptr)
    {
        OutReason = TEXT("bundle_directory_enumeration_failed");
        return false;
    }
    TArray<FString> Names;
    while (dirent* Entry = readdir(Directory))
    {
        const FString Name(UTF8_TO_TCHAR(Entry->d_name));
        if (Name != TEXT(".") && Name != TEXT("..")) Names.Add(Name);
    }
    closedir(Directory);
    Names.Sort();
    TArray<FString> Expected = {Row.PayloadName, Row.ProjectionName, Row.InvocationName};
    Expected.Sort();
    if (Names != Expected)
    {
        OutReason = TEXT("bundle_directory_member_set_mismatch");
        return false;
    }

    TSet<FString> DeviceInodes;
    for (const FString& Name : TArray<FString>({Row.PayloadName, Row.ProjectionName, Row.InvocationName}))
    {
        FTCHARToUTF8 NameUtf8(*Name);
        struct stat Info {};
        if (fstatat(OutDirectoryDescriptor, NameUtf8.Get(), &Info, AT_SYMLINK_NOFOLLOW) != 0 ||
            !S_ISREG(Info.st_mode) || S_ISLNK(Info.st_mode) || Info.st_nlink != 1)
        {
            OutReason = TEXT("bundle_member_not_distinct_regular_file");
            return false;
        }
        const FString Identity = FString::Printf(TEXT("%llu:%llu"),
            static_cast<unsigned long long>(Info.st_dev), static_cast<unsigned long long>(Info.st_ino));
        if (DeviceInodes.Contains(Identity))
        {
            OutReason = TEXT("bundle_member_hardlink_duplicate");
            return false;
        }
        DeviceInodes.Add(Identity);
        FCDOInputFileWitness File;
        File.Filename = Name;
        File.Realpath = FPaths::Combine(RootRealpath, Name);
        File.Device = static_cast<uint64>(Info.st_dev);
        File.Inode = static_cast<uint64>(Info.st_ino);
        File.Size = static_cast<int64>(Info.st_size);
        OutFiles.Add(MoveTemp(File));
    }
    return true;
}

bool FCrossDomainOccupancyProofAdapter::ReadBundleFile(
    int DirectoryDescriptor,
    FCDOInputFileWitness& File,
    FString& OutReason) const
{
    FTCHARToUTF8 NameUtf8(*File.Filename);
    const int Descriptor = openat(DirectoryDescriptor, NameUtf8.Get(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (Descriptor < 0)
    {
        OutReason = TEXT("bundle_member_open_failed");
        return false;
    }
    ON_SCOPE_EXIT { close(Descriptor); };
    struct stat Before {};
    if (fstat(Descriptor, &Before) != 0 || !S_ISREG(Before.st_mode) || Before.st_nlink != 1 ||
        Before.st_size < 3 || Before.st_size > 16 * 1024 * 1024 ||
        static_cast<uint64>(Before.st_dev) != File.Device || static_cast<uint64>(Before.st_ino) != File.Inode ||
        static_cast<int64>(Before.st_size) != File.Size)
    {
        OutReason = TEXT("bundle_member_pre_stat_mismatch");
        return false;
    }
    File.Bytes.SetNumUninitialized(static_cast<int32>(Before.st_size));
    ssize_t Total = 0;
    while (Total < Before.st_size)
    {
        const ssize_t Count = ::read(Descriptor, File.Bytes.GetData() + Total, static_cast<size_t>(Before.st_size - Total));
        if (Count <= 0)
        {
            OutReason = TEXT("bundle_member_short_read");
            return false;
        }
        Total += Count;
    }
    uint8 Trailing = 0;
    if (::read(Descriptor, &Trailing, 1) != 0)
    {
        OutReason = TEXT("bundle_member_trailing_read");
        return false;
    }
    struct stat After {};
    if (fstat(Descriptor, &After) != 0 || Before.st_dev != After.st_dev || Before.st_ino != After.st_ino ||
        Before.st_size != After.st_size || Before.st_mtimespec.tv_sec != After.st_mtimespec.tv_sec ||
        Before.st_mtimespec.tv_nsec != After.st_mtimespec.tv_nsec)
    {
        OutReason = TEXT("bundle_member_post_stat_mismatch");
        return false;
    }
    File.RawSha256 = Sha256Bytes(File.Bytes);
    return true;
}

bool FCrossDomainOccupancyProofAdapter::ValidateCandidateInputs(
    const FString& OperationId,
    const TArray<FCDOInputFileWitness>& Files,
    FCDOCandidateValues& OutCandidate,
    FString& OutReason) const
{
    if (Files.Num() != 3)
    {
        OutReason = TEXT("bundle_file_count_mismatch");
        return false;
    }
    FOperationRow Row;
    if (!OperationRow(Binding.DomainRole, OperationId, Row))
    {
        OutReason = TEXT("operation_tuple_mismatch");
        return false;
    }
    const FCDOInputFileWitness& PayloadFile = Files[0];
    const FCDOInputFileWitness& ProjectionFile = Files[1];
    const FCDOInputFileWitness& InvocationFile = Files[2];
    TSharedPtr<FJsonObject> Payload;
    TSharedPtr<FJsonObject> Projection;
    TSharedPtr<FJsonObject> Invocation;
    if (PayloadFile.Filename != Row.PayloadName || PayloadFile.RawSha256 != Row.PayloadDigest ||
        !StoredObject(PayloadFile.Bytes, Payload))
    {
        OutReason = TEXT("sealed_payload_identity_or_canonical_json_mismatch");
        return false;
    }
    if (ProjectionFile.Filename != Row.ProjectionName || ProjectionFile.RawSha256 != Row.ProjectionDigest ||
        !StoredObject(ProjectionFile.Bytes, Projection) || !HasExactKeys(Projection, {
            TEXT("allowed_site_projection"), TEXT("allowed_subject_projection"), TEXT("domain_role"),
            TEXT("projection_id"), TEXT("projection_schema"), TEXT("proof_scenario"), TEXT("source_canonical_hash")
        }) || !ExactString(Projection, TEXT("domain_role"), *Binding.DomainRole) ||
        !ExactString(Projection, TEXT("projection_id"), *Row.ProjectionId) ||
        !ExactString(Projection, TEXT("projection_schema"), TEXT("CrossDomainCanonicalOccupancyProjection.v1")) ||
        !ExactString(Projection, TEXT("proof_scenario"), Scenario) ||
        !ExactString(Projection, TEXT("source_canonical_hash"), *Row.TargetHash))
    {
        OutReason = TEXT("projection_identity_or_row_mismatch");
        return false;
    }
    if (InvocationFile.Filename != Row.InvocationName || !StoredObject(InvocationFile.Bytes, Invocation) ||
        !HasExactKeys(Invocation, {
            TEXT("domain_role"), TEXT("invocation_schema"), TEXT("operation"), TEXT("operation_id"),
            TEXT("operational_process_instance_id"), TEXT("proof_scenario"), TEXT("publication_generation"),
            TEXT("source_canonical_hash"), TEXT("target_canonical_hash"),
            TEXT("target_canonical_payload_raw_sha256"), TEXT("target_projection_id"),
            TEXT("target_projection_raw_sha256")
        }) || !ExactString(Invocation, TEXT("domain_role"), *Binding.DomainRole) ||
        !ExactString(Invocation, TEXT("invocation_schema"), TEXT("CrossDomainOccupancyOperationInvocation.v1")) ||
        !ExactString(Invocation, TEXT("operation"), *Row.Operation) ||
        !ExactString(Invocation, TEXT("operation_id"), *OperationId) ||
        !ExactString(Invocation, TEXT("operational_process_instance_id"), *Binding.OperationalProcessInstanceId) ||
        !ExactString(Invocation, TEXT("proof_scenario"), Scenario) ||
        !ExactString(Invocation, TEXT("publication_generation"), *Row.Generation) ||
        !ExactString(Invocation, TEXT("target_canonical_hash"), *Row.TargetHash) ||
        !ExactString(Invocation, TEXT("target_canonical_payload_raw_sha256"), *Row.PayloadDigest) ||
        !ExactString(Invocation, TEXT("target_projection_id"), *Row.ProjectionId) ||
        !ExactString(Invocation, TEXT("target_projection_raw_sha256"), *Row.ProjectionDigest) ||
        (Row.SourceHash.IsEmpty() ? !IsNullField(Invocation, TEXT("source_canonical_hash"))
                                  : !ExactString(Invocation, TEXT("source_canonical_hash"), *Row.SourceHash)))
    {
        OutReason = TEXT("operation_invocation_tuple_mismatch");
        return false;
    }

    const TSharedPtr<FJsonObject>* Current = nullptr;
    const TSharedPtr<FJsonObject>* Occupancies = nullptr;
    const TSharedPtr<FJsonObject>* Occupancy = nullptr;
    if (!Payload->TryGetObjectField(TEXT("current_causal_state"), Current) || !Current ||
        !(*Current)->TryGetObjectField(TEXT("canonical_occupancy"), Occupancies) || !Occupancies ||
        (*Occupancies)->Values.Num() != 1 || !(*Occupancies)->TryGetObjectField(Occupant, Occupancy) || !Occupancy)
    {
        OutReason = TEXT("canonical_occupancy_closed_shape_mismatch");
        return false;
    }
    FString Kind;
    if (!(*Occupancy)->TryGetStringField(TEXT("kind"), Kind))
    {
        OutReason = TEXT("canonical_occupancy_kind_missing");
        return false;
    }
    FString Reference;
    if (Kind == TEXT("at_site") && HasExactKeys(*Occupancy, {TEXT("kind"), TEXT("site_id")}) &&
        (*Occupancy)->TryGetStringField(TEXT("site_id"), Reference) && (Reference == SiteA || Reference == SiteB))
    {
    }
    else if (Kind == TEXT("in_transition") && HasExactKeys(*Occupancy, {TEXT("kind"), TEXT("transition_id")}) &&
        (*Occupancy)->TryGetStringField(TEXT("transition_id"), Reference) && Reference == Transition)
    {
    }
    else
    {
        OutReason = TEXT("canonical_occupancy_tagged_union_mismatch");
        return false;
    }
    const TSharedPtr<FJsonObject>* SiteProjection = nullptr;
    const TSharedPtr<FJsonObject>* SubjectProjection = nullptr;
    FString ProjectedSite;
    FString SiteSlot;
    FString SubjectSlot;
    FString ProjectedOccupant;
    if (!Projection->TryGetObjectField(TEXT("allowed_site_projection"), SiteProjection) || !SiteProjection ||
        !HasExactKeys(*SiteProjection, {TEXT("canonical_site_id"), TEXT("representation_slot")}) ||
        !(*SiteProjection)->TryGetStringField(TEXT("canonical_site_id"), ProjectedSite) ||
        !(*SiteProjection)->TryGetStringField(TEXT("representation_slot"), SiteSlot) ||
        !Projection->TryGetObjectField(TEXT("allowed_subject_projection"), SubjectProjection) || !SubjectProjection ||
        !HasExactKeys(*SubjectProjection, {TEXT("canonical_occupant_id"), TEXT("representation_slot")}) ||
        !(*SubjectProjection)->TryGetStringField(TEXT("canonical_occupant_id"), ProjectedOccupant) ||
        !(*SubjectProjection)->TryGetStringField(TEXT("representation_slot"), SubjectSlot) || ProjectedOccupant != Occupant)
    {
        OutReason = TEXT("projection_closed_member_mismatch");
        return false;
    }
    const FString ExpectedSite = Binding.DomainRole == TEXT("domain_A") ? SiteA : SiteB;
    const FString ExpectedSiteSlot = Binding.DomainRole == TEXT("domain_A") ? TEXT("domain_A_site_slot_01") : TEXT("domain_B_site_slot_01");
    const FString ExpectedSubjectSlot = Binding.DomainRole == TEXT("domain_A") ? TEXT("domain_A_subject_slot_01") : TEXT("domain_B_subject_slot_01");
    if (ProjectedSite != ExpectedSite || SiteSlot != ExpectedSiteSlot || SubjectSlot != ExpectedSubjectSlot)
    {
        OutReason = TEXT("role_projection_field_mismatch");
        return false;
    }
    FString Disposition;
    if (Kind == TEXT("in_transition")) Disposition = TEXT("in_transition_out_of_domain");
    else Disposition = Reference == ProjectedSite ? TEXT("present_at_local_site") : TEXT("remote_at_other_site");

    OutCandidate.DomainRole = Binding.DomainRole;
    OutCandidate.CanonicalPayloadRawSha256 = Row.PayloadDigest;
    OutCandidate.CanonicalHash = Row.TargetHash;
    OutCandidate.ProjectionRawSha256 = Row.ProjectionDigest;
    OutCandidate.ProjectionId = Row.ProjectionId;
    OutCandidate.ProjectedSiteId = ProjectedSite;
    OutCandidate.SiteSlot = SiteSlot;
    OutCandidate.SubjectSlot = SubjectSlot;
    OutCandidate.OccupancyKind = Kind;
    OutCandidate.OccupancyReference = Reference;
    OutCandidate.LocalDisposition = Disposition;
    OutCandidate.PublicationGeneration = Row.Generation;
    OutCandidate.Operation = Row.Operation;
    OutCandidate.OperationId = OperationId;
    OutCandidate.OperationInvocationRawSha256 = InvocationFile.RawSha256;
    OutCandidate.bSubjectRequired = Disposition == TEXT("present_at_local_site");
    return true;
}

bool FCrossDomainOccupancyProofAdapter::DestroyPredecessorGeneration(FString& OutReason)
{
    UWorld* ExactWorld = World.Get();
    if (ExactWorld == nullptr)
    {
        OutReason = TEXT("process_world_unavailable");
        return false;
    }
    TArray<AActor*> Predecessors;
    for (ULevel* Level : ExactWorld->GetLevels())
    {
        if (Level == nullptr) continue;
        for (const TObjectPtr<AActor>& Slot : Level->Actors)
        {
            AActor* Actor = Slot.Get();
            if (Cast<ACrossDomainOccupancyHeadAnchorActor>(Actor) != nullptr ||
                Cast<ACrossDomainOccupancySubjectActor>(Actor) != nullptr) Predecessors.Add(Actor);
        }
    }
    for (AActor* Actor : Predecessors)
    {
        if (!ExactWorld->DestroyActor(Actor, true, true))
        {
            OutReason = TEXT("predecessor_destroy_failed");
            return false;
        }
    }
    PublishedAnchor.Reset();
    PublishedSubject.Reset();
    for (ULevel* Level : ExactWorld->GetLevels())
    {
        if (Level == nullptr) continue;
        for (const TObjectPtr<AActor>& Slot : Level->Actors)
        {
            AActor* Actor = Slot.Get();
            if (Cast<ACrossDomainOccupancyHeadAnchorActor>(Actor) != nullptr ||
                Cast<ACrossDomainOccupancySubjectActor>(Actor) != nullptr)
            {
                OutReason = TEXT("predecessor_generation_still_in_loaded_level_actor_slots");
                return false;
            }
        }
    }
    return true;
}

bool FCrossDomainOccupancyProofAdapter::SpawnSubject(const FCDOCandidateValues& Candidate, FString& OutReason)
{
    if (!Candidate.bSubjectRequired) return true;
    UWorld* ExactWorld = World.Get();
    if (ExactWorld == nullptr) return false;
    ACrossDomainOccupancySubjectActor* Actor = ExactWorld->SpawnActorDeferred<ACrossDomainOccupancySubjectActor>(
        ACrossDomainOccupancySubjectActor::StaticClass(), FTransform::Identity, nullptr, nullptr,
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (Actor == nullptr || !Actor->ConfigureExact(
        Candidate.DomainRole, Binding.OperationalProcessInstanceId, Binding.ProcessBindingRawSha256,
        Candidate.CanonicalPayloadRawSha256, Candidate.CanonicalHash, Candidate.ProjectionRawSha256,
        Candidate.ProjectionId, Candidate.ProjectedSiteId, Candidate.SubjectSlot,
        Candidate.PublicationGeneration))
    {
        if (Actor != nullptr) Actor->Destroy();
        OutReason = TEXT("target_subject_configuration_failed");
        return false;
    }
    Actor->FinishSpawning(FTransform::Identity);
    PublishedSubject = Actor;
    return true;
}

bool FCrossDomainOccupancyProofAdapter::SpawnAnchor(const FCDOCandidateValues& Candidate, FString& OutReason)
{
    UWorld* ExactWorld = World.Get();
    if (ExactWorld == nullptr) return false;
    ACrossDomainOccupancyHeadAnchorActor* Actor = ExactWorld->SpawnActorDeferred<ACrossDomainOccupancyHeadAnchorActor>(
        ACrossDomainOccupancyHeadAnchorActor::StaticClass(), FTransform::Identity, nullptr, nullptr,
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (Actor == nullptr || !Actor->ConfigureExact(
        Candidate.DomainRole, Binding.OperationalProcessInstanceId, Binding.ProcessBindingRawSha256,
        Candidate.CanonicalPayloadRawSha256, Candidate.CanonicalHash, Candidate.ProjectionRawSha256,
        Candidate.ProjectionId, Candidate.ProjectedSiteId, Candidate.SiteSlot, Candidate.SubjectSlot,
        Candidate.OccupancyKind, Candidate.OccupancyReference, Candidate.LocalDisposition,
        Candidate.PublicationGeneration))
    {
        if (Actor != nullptr) Actor->Destroy();
        OutReason = TEXT("target_anchor_configuration_failed");
        return false;
    }
    Actor->FinishSpawning(FTransform::Identity);
    PublishedAnchor = Actor;
    return true;
}

bool FCrossDomainOccupancyProofAdapter::ValidatePublishedGeneration(
    const FCDOCandidateValues& Candidate,
    FString& OutReason) const
{
    UWorld* ExactWorld = World.Get();
    if (ExactWorld == nullptr) return false;
    int32 Anchors = 0;
    int32 Subjects = 0;
    for (ULevel* Level : ExactWorld->GetLevels())
    {
        if (Level == nullptr) continue;
        for (const TObjectPtr<AActor>& Slot : Level->Actors)
        {
            AActor* Actor = Slot.Get();
            if (ACrossDomainOccupancyHeadAnchorActor* Anchor = Cast<ACrossDomainOccupancyHeadAnchorActor>(Actor))
            {
                ++Anchors;
                if (Anchor->GetPublicationGeneration() != Candidate.PublicationGeneration)
                {
                    OutReason = TEXT("anchor_generation_mismatch");
                    return false;
                }
            }
            if (ACrossDomainOccupancySubjectActor* Subject = Cast<ACrossDomainOccupancySubjectActor>(Actor))
            {
                ++Subjects;
                if (Subject->GetPublicationGeneration() != Candidate.PublicationGeneration)
                {
                    OutReason = TEXT("subject_generation_mismatch");
                    return false;
                }
            }
        }
    }
    if (Anchors != 1 || Subjects != (Candidate.bSubjectRequired ? 1 : 0))
    {
        OutReason = TEXT("adapter_visible_generation_cardinality_mismatch");
        return false;
    }
    return true;
}

TSharedPtr<FJsonObject> FCrossDomainOccupancyProofAdapter::BuildReceipt(
    const FCDOCandidateValues& Candidate,
    const FString& CommandRawSha256,
    bool bPrivateCandidate) const
{
    TArray<TSharedPtr<FJsonValue>> AnchorRows;
    TArray<TSharedPtr<FJsonValue>> SubjectRows;
    if (bPrivateCandidate)
    {
        AnchorRows.Add(ObjectValue(PrivateAnchorRow(Candidate, Binding)));
        if (Candidate.bSubjectRequired) SubjectRows.Add(ObjectValue(PrivateSubjectRow(Candidate, Binding)));
    }
    else
    {
        if (PublishedAnchor.IsValid()) AnchorRows.Add(ObjectValue(PublishedAnchor->BuildLiveFieldRow()));
        if (PublishedSubject.IsValid()) SubjectRows.Add(ObjectValue(PublishedSubject->BuildLiveFieldRow()));
    }
    TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
    Receipt->SetStringField(TEXT("accepted_canonical_hash"), Candidate.CanonicalHash);
    Receipt->SetStringField(TEXT("accepted_canonical_payload_raw_sha256"), Candidate.CanonicalPayloadRawSha256);
    Receipt->SetStringField(TEXT("accepted_projection_id"), Candidate.ProjectionId);
    Receipt->SetStringField(TEXT("accepted_projection_raw_sha256"), Candidate.ProjectionRawSha256);
    Receipt->SetStringField(TEXT("canonical_occupancy_kind"), Candidate.OccupancyKind);
    Receipt->SetStringField(TEXT("canonical_occupancy_reference"), Candidate.OccupancyReference);
    Receipt->SetStringField(TEXT("canonical_occupant_id"), Occupant);
    Receipt->SetStringField(TEXT("derived_local_subject_disposition"), Candidate.LocalDisposition);
    Receipt->SetStringField(TEXT("domain_role"), Candidate.DomainRole);
    Receipt->SetStringField(TEXT("materialize_command_raw_sha256"), CommandRawSha256);
    Receipt->SetStringField(TEXT("operation"), Candidate.Operation);
    Receipt->SetStringField(TEXT("operation_id"), Candidate.OperationId);
    Receipt->SetStringField(TEXT("operation_invocation_raw_sha256"), Candidate.OperationInvocationRawSha256);
    Receipt->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    Receipt->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
    Receipt->SetStringField(TEXT("projected_canonical_site_id"), Candidate.ProjectedSiteId);
    Receipt->SetStringField(TEXT("projected_site_representation_slot"), Candidate.SiteSlot);
    Receipt->SetStringField(TEXT("projected_subject_representation_slot"), Candidate.SubjectSlot);
    Receipt->SetStringField(TEXT("proof_scenario"), Scenario);
    Receipt->SetStringField(TEXT("publication_generation"), Candidate.PublicationGeneration);
    Receipt->SetNumberField(TEXT("published_anchor_actor_count"), AnchorRows.Num());
    Receipt->SetArrayField(TEXT("published_anchor_actor_rows"), AnchorRows);
    Receipt->SetNumberField(TEXT("published_subject_actor_count"), SubjectRows.Num());
    Receipt->SetArrayField(TEXT("published_subject_actor_rows"), SubjectRows);
    Receipt->SetStringField(TEXT("receipt_authority"), TEXT("representation_only"));
    Receipt->SetStringField(TEXT("receipt_schema"), TEXT("CrossDomainOccupancyMaterializationReceipt.v1"));
    Receipt->SetStringField(TEXT("representation_publication_state"), TEXT("locally_published_unverified"));
    return Receipt;
}

bool FCrossDomainOccupancyProofAdapter::MaterializeOnce(
    const FString& OperationId,
    const FString& RelativeBundleRoot,
    const FString& CommandRawSha256,
    FCDOInjectedFaultPlan* FaultPlan,
    TSharedPtr<FJsonObject>& OutReceipt,
    FString& OutReason)
{
    int DirectoryDescriptor = -1;
    TArray<FCDOInputFileWitness> Files;
    TSharedPtr<FJsonObject> Payload;
    TSharedPtr<FJsonObject> Projection;
    TSharedPtr<FJsonObject> Invocation;
    FCDOCandidateValues Candidate;
    bool bPublicationBegan = false;
    ON_SCOPE_EXIT { if (DirectoryDescriptor >= 0) close(DirectoryDescriptor); };
    auto Failed = [&]()
    {
        if (bPublicationBegan) PublicationState = TEXT("invalid");
        return false;
    };

    if (!Stage(TEXT("M02_resolve_role_private_bundle_root"), FaultPlan, [&]()
        {
            FOperationRow Row;
            return OperationRow(Binding.DomainRole, OperationId, Row) && RelativeBundleRoot == Row.RelativeRoot;
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M03_inventory_exact_three_file_directory"), FaultPlan, [&]()
        {
            return InventoryBundle(OperationId, RelativeBundleRoot, DirectoryDescriptor, Files, OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M04_open_and_pre_stat_payload"), FaultPlan, [&]()
        {
            return Files.Num() == 3 && ReadBundleFile(DirectoryDescriptor, Files[0], OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M05_read_and_post_stat_payload"), FaultPlan, []() { return true; }, OutReason,
        {ObjectValue(FileWitnessRow(Files[0]))})) return Failed();
    if (!Stage(TEXT("M06_authenticate_and_validate_payload"), FaultPlan, [&]()
        {
            FOperationRow Row;
            if (!OperationRow(Binding.DomainRole, OperationId, Row) || Files[0].RawSha256 != Row.PayloadDigest)
            {
                OutReason = TEXT("sealed_payload_identity_mismatch");
                return false;
            }
            if (!StoredObject(Files[0].Bytes, Payload))
            {
                OutReason = TEXT("canonical_shape_mismatch");
                return false;
            }
            return true;
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M07_open_and_pre_stat_projection"), FaultPlan, [&]()
        {
            return ReadBundleFile(DirectoryDescriptor, Files[1], OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M08_read_and_post_stat_projection"), FaultPlan, []() { return true; }, OutReason,
        {ObjectValue(FileWitnessRow(Files[1]))})) return Failed();
    if (!Stage(TEXT("M09_authenticate_and_validate_projection"), FaultPlan, [&]()
        {
            FOperationRow Row;
            if (!OperationRow(Binding.DomainRole, OperationId, Row) || Files[1].RawSha256 != Row.ProjectionDigest)
            {
                OutReason = TEXT("projection_raw_sha256_not_frozen");
                return false;
            }
            if (!StoredObject(Files[1].Bytes, Projection))
            {
                OutReason = TEXT("projection_canonical_json_mismatch");
                return false;
            }
            return true;
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M10_open_and_pre_stat_invocation"), FaultPlan, [&]()
        {
            return ReadBundleFile(DirectoryDescriptor, Files[2], OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M11_read_and_post_stat_invocation"), FaultPlan, []() { return true; }, OutReason,
        {ObjectValue(FileWitnessRow(Files[2]))})) return Failed();
    if (!Stage(TEXT("M12_validate_operation_tuple_and_process_binding"), FaultPlan, [&]()
        {
            return ValidateCandidateInputs(OperationId, Files, Candidate, OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M13_derive_local_subject_disposition"), FaultPlan, [&]()
        {
            return !Candidate.LocalDisposition.IsEmpty();
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M14_construct_private_anchor_values"), FaultPlan, [&]()
        {
            return PrivateAnchorRow(Candidate, Binding).IsValid();
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M15_construct_private_subject_values"), FaultPlan, [&]()
        {
            return !Candidate.bSubjectRequired || PrivateSubjectRow(Candidate, Binding).IsValid();
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M16_validate_candidate_coherence_and_cardinality"), FaultPlan, [&]()
        {
            return Candidate.PublicationGeneration != PublicationGeneration &&
                (OperationId == TEXT("launch_0001") ? PublicationGeneration.IsEmpty() : !PublicationGeneration.IsEmpty());
        }, OutReason))
    {
        if (FaultPlan != nullptr && FaultPlan->bInjected && FaultPlan->CaseId == TEXT("control_C3") &&
            FaultPlan->StageId == TEXT("M16_validate_candidate_coherence_and_cardinality") && FaultPlan->Edge == TEXT("after"))
        {
            OutReceipt = BuildReceipt(Candidate, CommandRawSha256, true);
        }
        return Failed();
    }
    if (!Stage(TEXT("M17_begin_publication_linearization_interval"), FaultPlan, [&]()
        {
            bPublicationBegan = true;
            PublicationState = TEXT("publication_in_progress");
            return true;
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M18_destroy_and_verify_predecessor_generation_absent"), FaultPlan, [&]()
        {
            return DestroyPredecessorGeneration(OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M19_spawn_configure_and_finish_target_subject_set"), FaultPlan, [&]()
        {
            return SpawnSubject(Candidate, OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M20_spawn_configure_and_finish_target_anchor"), FaultPlan, [&]()
        {
            return SpawnAnchor(Candidate, OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M21_enumerate_and_validate_adapter_visible_generation"), FaultPlan, [&]()
        {
            return ValidatePublishedGeneration(Candidate, OutReason);
        }, OutReason)) return Failed();
    if (!Stage(TEXT("M22_emit_materialization_receipt"), FaultPlan, [&]()
        {
            OutReceipt = BuildReceipt(Candidate, CommandRawSha256, false);
            return OutReceipt.IsValid();
        }, OutReason, {}, OutReceipt)) return Failed();

    RepresentedCanonicalHash = Candidate.CanonicalHash;
    PublicationGeneration = Candidate.PublicationGeneration;
    PublicationState = TEXT("locally_published_unverified");
    return true;
}
