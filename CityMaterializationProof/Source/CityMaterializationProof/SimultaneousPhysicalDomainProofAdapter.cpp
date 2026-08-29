#include "SimultaneousPhysicalDomainProofAdapter.h"

#include "SimultaneousPhysicalDomainRepresentationActor.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"

#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

namespace
{
using namespace SimultaneousPhysicalDomainJson;

constexpr TCHAR Scenario[] = TEXT("simultaneous-physical-domains-v1.1");
constexpr TCHAR H0[] = TEXT("666d75281d3478e586edd12464d2736169f423c2d7b128bd3d2d2b1b2b826b29");
constexpr TCHAR H1[] = TEXT("78cc5ffe0c4758c296d8fee0bc2a95e230be0bec0a4aab680806eb670500804a");
constexpr TCHAR D0[] = TEXT("5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed");
constexpr TCHAR D1[] = TEXT("7ac7ece5c142ac4dee83abc6e83f7845d85dfc7f055ca6d678b7f04bdf1d795a");
constexpr TCHAR RouteId[] = TEXT("topology_route_0001");
constexpr TCHAR SiteA[] = TEXT("topology_site_0001");
constexpr TCHAR SiteB[] = TEXT("topology_site_0002");

bool ExactNull(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field)
{
    const TSharedPtr<FJsonValue>* Value = Object.IsValid() ? Object->Values.Find(Field) : nullptr;
    return Value != nullptr && Value->IsValid() && (*Value)->IsNull();
}

bool ExactStringArray2(const TArray<TSharedPtr<FJsonValue>>& Values, const TCHAR* A, const TCHAR* B)
{
    FString First;
    FString Second;
    return Values.Num() == 2 && Values[0].IsValid() && Values[1].IsValid() &&
        Values[0]->TryGetString(First) && Values[1]->TryGetString(Second) && First == A && Second == B;
}

bool StrictDirectory(const FString& Root, const TArray<FString>& Expected, FString& OutReason)
{
    struct stat RootInfo {};
    FTCHARToUTF8 RootUtf8(*Root);
    if (lstat(RootUtf8.Get(), &RootInfo) != 0 || !S_ISDIR(RootInfo.st_mode) || S_ISLNK(RootInfo.st_mode))
    {
        OutReason = TEXT("visible_input_directory_invalid");
        return false;
    }
    TArray<FString> Entries;
    IFileManager::Get().FindFiles(Entries, *(FPaths::Combine(Root, TEXT("*"))), true, true);
    Entries.Sort();
    TArray<FString> SortedExpected(Expected);
    SortedExpected.Sort();
    if (Entries != SortedExpected)
    {
        OutReason = TEXT("visible_input_member_set_mismatch");
        return false;
    }
    TSet<FString> DeviceInodes;
    for (const FString& Name : Expected)
    {
        const FString Path = FPaths::Combine(Root, Name);
        FTCHARToUTF8 PathUtf8(*Path);
        struct stat Info {};
        if (lstat(PathUtf8.Get(), &Info) != 0 || !S_ISREG(Info.st_mode) || S_ISLNK(Info.st_mode) || Info.st_nlink != 1)
        {
            OutReason = TEXT("visible_input_nonregular_or_linked");
            return false;
        }
        const FString Identity = FString::Printf(TEXT("%llu:%llu"),
            static_cast<unsigned long long>(Info.st_dev), static_cast<unsigned long long>(Info.st_ino));
        if (DeviceInodes.Contains(Identity))
        {
            OutReason = TEXT("visible_input_hardlink_duplicate");
            return false;
        }
        DeviceInodes.Add(Identity);
    }
    FString DirectoryRealpath = FPaths::ConvertRelativePathToFull(Root);
    FPaths::NormalizeDirectoryName(DirectoryRealpath);
    SimultaneousPhysicalDomainRuntimeAudit::RecordDirectoryInventory(DirectoryRealpath, Entries);
    return true;
}

TSharedPtr<FJsonValue> StringValue(const FString& Value)
{
    return MakeShared<FJsonValueString>(Value);
}

bool LoadStoredBytesNoFollow(const FString& Path, TArray<uint8>& OutBytes)
{
    FTCHARToUTF8 PathUtf8(*Path);
    const int Descriptor = open(PathUtf8.Get(), O_RDONLY | O_NOFOLLOW);
    if (Descriptor < 0)
    {
        return false;
    }
    struct stat Info {};
    if (fstat(Descriptor, &Info) != 0 || !S_ISREG(Info.st_mode) || Info.st_nlink != 1 ||
        Info.st_size < 3 || Info.st_size > 16 * 1024 * 1024)
    {
        close(Descriptor);
        return false;
    }
    OutBytes.SetNumUninitialized(static_cast<int32>(Info.st_size));
    ssize_t Total = 0;
    while (Total < Info.st_size)
    {
        const ssize_t Read = ::read(
            Descriptor, OutBytes.GetData() + Total,
            static_cast<size_t>(Info.st_size - Total));
        if (Read <= 0)
        {
            close(Descriptor);
            return false;
        }
        Total += Read;
    }
    close(Descriptor);
    FString FileRealpath = FPaths::ConvertRelativePathToFull(Path);
    FPaths::NormalizeFilename(FileRealpath);
    SimultaneousPhysicalDomainRuntimeAudit::RecordBundleFileRead(
        FileRealpath,
        Sha256Bytes(OutBytes),
        static_cast<int64>(Info.st_size),
        static_cast<uint64>(Info.st_dev),
        static_cast<uint64>(Info.st_ino));
    if (OutBytes.Last() != '\n')
    {
        return false;
    }
    int32 Newlines = 0;
    for (uint8 Byte : OutBytes)
    {
        if (Byte == '\r') return false;
        if (Byte == '\n') ++Newlines;
    }
    return Newlines == 1;
}

bool ParseStoredObject(const TArray<uint8>& Bytes, TSharedPtr<FJsonObject>& OutObject)
{
    if (Bytes.Num() < 3 || Bytes.Last() != '\n')
    {
        return false;
    }
    FUTF8ToTCHAR Converted(
        reinterpret_cast<const ANSICHAR*>(Bytes.GetData()), Bytes.Num() - 1);
    return ParseCanonicalObject(FString(Converted.Length(), Converted.Get()), OutObject);
}
}

ASimultaneousPhysicalDomainProofAdapter::ASimultaneousPhysicalDomainProofAdapter()
{
    PrimaryActorTick.bCanEverTick = false;
}

bool ASimultaneousPhysicalDomainProofAdapter::MaterializeLaunch(
    const FSPDImmutableProcessBinding& Binding,
    TSharedPtr<FJsonObject>& OutReceipt,
    FString& OutReason)
{
    if (!RepresentedCanonicalHash.IsEmpty() || PublishedRepresentation != nullptr)
    {
        OutReason = TEXT("launch_materialization_already_consumed");
        return false;
    }
    FSPDValidatedVisibleTuple Tuple;
    FSPDAuthoritativeRepresentation Candidate;
    if (!LoadVisibleTuple(Binding, false, Tuple, nullptr, OutReason) ||
        !BuildAuthoritativeCandidate(Tuple.Payload, Tuple.Projection, Candidate, nullptr, OutReason))
    {
        return false;
    }
    bRetentionWitness = Binding.WitnessId == TEXT("w5_retention_baseline") ||
        Binding.WitnessId == TEXT("w5_retention_perturbed");
    bPerturbedRetentionWitness = Binding.WitnessId == TEXT("w5_retention_perturbed");
    if (bPerturbedRetentionWitness)
    {
        NonconsequentialTickCounter = 991;
        CosmeticPhaseToken = TEXT("cosmetic_phase_3");
        DiagnosticCounter = 47;
    }
    else
    {
        NonconsequentialTickCounter = 7;
        CosmeticPhaseToken = TEXT("cosmetic_phase_0");
        DiagnosticCounter = 1;
    }
    if (!PublishCandidate(Candidate, Binding, OutReceipt, OutReason))
    {
        return false;
    }
    if (bRetentionWitness && !PublishedRepresentation->InstallDiscardRequiredH0Poison(bPerturbedRetentionWitness))
    {
        OutReason = TEXT("discard_required_H0_poison_installation_failed");
        return false;
    }
    return true;
}

bool ASimultaneousPhysicalDomainProofAdapter::RefreshOnce(
    const FSPDImmutableProcessBinding& Binding,
    FSPDInjectedFaultPlan* FaultPlan,
    TSharedPtr<FJsonObject>& OutReceipt,
    FString& OutReason)
{
    if (bRefreshConsumed || RepresentedCanonicalHash != H0 || PublishedRepresentation == nullptr)
    {
        OutReason = TEXT("refresh_not_exactly_once_from_H0");
        return false;
    }
    bRefreshConsumed = true;
    ASimultaneousPhysicalDomainRepresentationActor* PriorH0Representation = PublishedRepresentation;

    FSPDValidatedVisibleTuple Tuple;
    if (!LoadVisibleTuple(Binding, true, Tuple, FaultPlan, OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("process_binding_identity_verification"), TEXT("before"), OutReason))
    {
        return false;
    }
    if (Binding.DomainRole != TEXT("domain_A") && Binding.DomainRole != TEXT("domain_B") ||
        Binding.OperationalProcessInstanceId.Len() != 64 ||
        Binding.ProcessBindingRawSha256.Len() != 64 ||
        Binding.ExecutableRawSha256.Len() != 64 || Binding.CompleteBinding == nullptr)
    {
        OutReason = TEXT("refresh_process_binding_identity_invalid");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("process_binding_identity_verification"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("retained_local_state_projection_extraction"), TEXT("before"), OutReason))
    {
        return false;
    }
    const uint64 RetainedTick = NonconsequentialTickCounter;
    const FString RetainedCosmetic = CosmeticPhaseToken;
    const uint64 RetainedDiagnostic = DiagnosticCounter;
    if (RetainedCosmetic != TEXT("cosmetic_phase_0") && RetainedCosmetic != TEXT("cosmetic_phase_1") &&
        RetainedCosmetic != TEXT("cosmetic_phase_2") && RetainedCosmetic != TEXT("cosmetic_phase_3"))
    {
        OutReason = TEXT("retained_local_state_projection_invalid");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("retained_local_state_projection_extraction"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("discard_required_state_poison_check"), TEXT("before"), OutReason))
    {
        return false;
    }
    if (bRetentionWitness)
    {
        bPoisonObservedBeforeRefresh = PriorH0Representation->HasExactDiscardRequiredH0Poison(
            bPerturbedRetentionWitness);
        if (!bPoisonObservedBeforeRefresh)
        {
            OutReason = TEXT("discard_required_H0_poison_not_observed");
            return false;
        }
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("discard_required_state_poison_check"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("empty_authoritative_candidate_construction"), TEXT("before"), OutReason))
    {
        return false;
    }
    FSPDAuthoritativeRepresentation Candidate;
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("empty_authoritative_candidate_construction"), TEXT("after"), OutReason))
    {
        return false;
    }
    if (!BuildAuthoritativeCandidate(Tuple.Payload, Tuple.Projection, Candidate, FaultPlan, OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("retained_local_state_attachment"), TEXT("before"), OutReason))
    {
        return false;
    }
    // Candidate construction and validation above receive no retained value.
    // The whitelisted scalars are attached only to adapter-local state.
    NonconsequentialTickCounter = RetainedTick;
    CosmeticPhaseToken = RetainedCosmetic;
    DiagnosticCounter = RetainedDiagnostic;
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("retained_local_state_attachment"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("prepublication_cross_field_validation"), TEXT("before"), OutReason))
    {
        return false;
    }
    if (Candidate.CanonicalHash != H1 || Candidate.RawPayloadHash != D1 ||
        Candidate.AccessState != TEXT("blocked") || Candidate.DomainRole != Binding.DomainRole)
    {
        OutReason = TEXT("prepublication_cross_field_validation_failed");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("prepublication_cross_field_validation"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("local_atomic_publication"), TEXT("before"), OutReason))
    {
        return false;
    }
    if (!PublishCandidate(Candidate, Binding, OutReceipt, OutReason))
    {
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("local_atomic_publication"), TEXT("after"), OutReason))
    {
        return false;
    }
    if (bRetentionWitness)
    {
        bPriorH0ActorReplaced = PublishedRepresentation != PriorH0Representation;
        bPublishedH1PoisonClear = PublishedRepresentation != nullptr &&
            PublishedRepresentation->IsDiscardRequiredPoisonClear();
        if (!bPriorH0ActorReplaced || !bPublishedH1PoisonClear)
        {
            OutReason = TEXT("discard_required_state_survived_H1_publication");
            return false;
        }
    }
    return true;
}

bool ASimultaneousPhysicalDomainProofAdapter::ExecuteNonconsequentialStepOnce(
    const FSPDImmutableProcessBinding& Binding,
    TSharedPtr<FJsonObject>& OutObservation,
    FString& OutReason)
{
    if (bLocalStepConsumed || Binding.WitnessId != TEXT("w3_stale_quarantine") ||
        RepresentedCanonicalHash != H0 || PublishedRepresentation == nullptr ||
        NonconsequentialTickCounter >= 9007199254740990ULL)
    {
        OutReason = TEXT("local_step_precondition_invalid");
        return false;
    }
    bLocalStepConsumed = true;
    ASimultaneousPhysicalDomainRepresentationActor* const ActorBefore = PublishedRepresentation;
    const uint64 CounterBefore = NonconsequentialTickCounter;
    ++NonconsequentialTickCounter;

    OutObservation = MakeShared<FJsonObject>();
    OutObservation->SetStringField(TEXT("observation_schema"), TEXT("SimultaneousPhysicalDomainLocalStepObservation.v1"));
    OutObservation->SetStringField(TEXT("proof_scenario"), Scenario);
    OutObservation->SetStringField(TEXT("domain_role"), Binding.DomainRole);
    OutObservation->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    OutObservation->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
    OutObservation->SetStringField(TEXT("step_id"), TEXT("stale_quarantine_step_0001"));
    OutObservation->SetStringField(TEXT("step_name"), TEXT("increment_nonconsequential_tick_counter_once"));
    OutObservation->SetNumberField(TEXT("counter_before"), static_cast<double>(CounterBefore));
    OutObservation->SetNumberField(TEXT("counter_after"), static_cast<double>(NonconsequentialTickCounter));
    OutObservation->SetStringField(TEXT("represented_hash_before"), H0);
    OutObservation->SetStringField(TEXT("represented_hash_after"), RepresentedCanonicalHash);
    OutObservation->SetBoolField(TEXT("published_actor_identity_unchanged"), ActorBefore == PublishedRepresentation);
    OutObservation->SetNumberField(TEXT("materialization_receipt_count_delta"), 0);
    OutObservation->SetNumberField(TEXT("canonical_evidence_count_delta"), 0);
    OutObservation->SetNumberField(TEXT("canonical_scheduling_count_delta"), 0);
    OutObservation->SetNumberField(TEXT("canonical_mutation_count_delta"), 0);
    OutObservation->SetNumberField(TEXT("canonical_truth_claim_count_delta"), 0);
    OutObservation->SetStringField(TEXT("observation_source"), TEXT("live_ue_adapter_exact_local_step"));
    return true;
}

FString ASimultaneousPhysicalDomainProofAdapter::GetPublicationState() const
{
    if (RepresentedCanonicalHash == H1 && PublishedRepresentation != nullptr) return TEXT("H1_published");
    if (RepresentedCanonicalHash == H0 && PublishedRepresentation != nullptr) return TEXT("H0_published");
    return TEXT("none");
}

TSharedPtr<FJsonObject> ASimultaneousPhysicalDomainProofAdapter::BuildRetentionExecutionObservation(
    const FSPDImmutableProcessBinding& Binding) const
{
    if (!bRetentionWitness || RepresentedCanonicalHash != H1 || !bPoisonObservedBeforeRefresh ||
        !bPublishedH1PoisonClear || !bPriorH0ActorReplaced || PublishedRepresentation == nullptr)
    {
        return nullptr;
    }
    TSharedPtr<FJsonObject> Observation = MakeShared<FJsonObject>();
    Observation->SetStringField(TEXT("observation_schema"), TEXT("SimultaneousPhysicalDomainRetentionExecutionObservation.v1"));
    Observation->SetStringField(TEXT("proof_scenario"), Scenario);
    Observation->SetStringField(TEXT("domain_role"), Binding.DomainRole);
    Observation->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    Observation->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
    Observation->SetStringField(TEXT("branch"), bPerturbedRetentionWitness ? TEXT("perturbed") : TEXT("baseline"));
    Observation->SetNumberField(TEXT("retained_nonconsequential_tick_counter"), static_cast<double>(NonconsequentialTickCounter));
    Observation->SetStringField(TEXT("retained_cosmetic_phase_token"), CosmeticPhaseToken);
    Observation->SetNumberField(TEXT("retained_diagnostic_counter"), static_cast<double>(DiagnosticCounter));
    Observation->SetBoolField(TEXT("discard_required_H0_poison_observed_before_refresh"), bPoisonObservedBeforeRefresh);
    Observation->SetBoolField(TEXT("prior_H0_actor_replaced"), bPriorH0ActorReplaced);
    Observation->SetBoolField(TEXT("published_H1_actor_poison_clear"), bPublishedH1PoisonClear);
    Observation->SetBoolField(TEXT("poisoned_actor_ids_discarded"), true);
    Observation->SetBoolField(TEXT("poisoned_topology_cache_discarded"), true);
    Observation->SetBoolField(TEXT("poisoned_route_access_cache_discarded"), true);
    Observation->SetBoolField(TEXT("poisoned_collision_state_discarded"), true);
    Observation->SetBoolField(TEXT("poisoned_physics_diagnostics_discarded"), true);
    Observation->SetStringField(TEXT("represented_canonical_hash"), H1);
    Observation->SetStringField(TEXT("observation_source"), TEXT("live_ue_adapter_postpublication_state_inspection"));
    return Observation;
}

bool ASimultaneousPhysicalDomainProofAdapter::LoadVisibleTuple(
    const FSPDImmutableProcessBinding& Binding,
    bool bRefresh,
    FSPDValidatedVisibleTuple& OutTuple,
    FSPDInjectedFaultPlan* FaultPlan,
    FString& OutReason) const
{
    const FString HeadRole = bRefresh ? TEXT("H1") : TEXT("H0");
    const FString Operation = bRefresh ? TEXT("refresh") : TEXT("launch");
    const FString Directory = FPaths::Combine(
        Binding.ProcessRootRealpath,
        bRefresh ? TEXT("refresh_input/refresh_0001") : TEXT("launch_input/launch_0001"));
    const FString RoleToken = Binding.DomainRole == TEXT("domain_A") ? TEXT("A") : TEXT("B");
    const FString PayloadName = bRefresh ? TEXT("canonical_topology_R1.json") : TEXT("canonical_topology_R0.json");
    const FString ProjectionName = FString::Printf(TEXT("simultaneous_domain_%s_%s_projection.json"), *RoleToken, *HeadRole);
    const FString ReceiptName = FString::Printf(TEXT("simultaneous_domain_%s_%s_operation_receipt.json"), *RoleToken, *HeadRole);
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("visible_input_inventory"), TEXT("before"), OutReason))
    {
        return false;
    }
    if (!StrictDirectory(Directory, {PayloadName, ProjectionName, ReceiptName}, OutReason))
    {
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("visible_input_inventory"), TEXT("after"), OutReason))
    {
        return false;
    }

    TArray<uint8> PayloadBytes;
    TArray<uint8> ProjectionBytes;
    TArray<uint8> ReceiptBytes;
    const FString ExpectedRawPayload = bRefresh ? D1 : D0;
    const FString ExpectedHash = bRefresh ? H1 : H0;

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("payload_raw_byte_verification"), TEXT("before"), OutReason))
    {
        return false;
    }
    if (!LoadStoredBytesNoFollow(FPaths::Combine(Directory, PayloadName), PayloadBytes) ||
        Sha256Bytes(PayloadBytes) != ExpectedRawPayload)
    {
        OutReason = TEXT("payload_raw_sha256_mismatch");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("payload_raw_byte_verification"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("payload_parse_and_canonical_identity_verification"), TEXT("before"), OutReason))
    {
        return false;
    }
    TSharedPtr<FJsonObject> Payload;
    if (!ParseStoredObject(PayloadBytes, Payload))
    {
        OutReason = TEXT("payload_parse_failure");
        return false;
    }
    TArray<uint8> PayloadCanonicalBytes(PayloadBytes);
    PayloadCanonicalBytes.Pop();
    if (Sha256Bytes(PayloadCanonicalBytes) != ExpectedHash)
    {
        OutReason = TEXT("payload_canonical_hash_mismatch");
        return false;
    }

    const TSharedPtr<FJsonObject>* Identity = nullptr;
    const TSharedPtr<FJsonObject>* Current = nullptr;
    const TSharedPtr<FJsonObject>* Topology = nullptr;
    const TSharedPtr<FJsonObject>* Sites = nullptr;
    const TSharedPtr<FJsonObject>* Routes = nullptr;
    const TSharedPtr<FJsonObject>* Route = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Endpoints = nullptr;
    if (!HasExactKeys(Payload, {TEXT("identity"), TEXT("current_causal_state"), TEXT("future_causal_state"), TEXT("causal_provenance")}) ||
        !Payload->TryGetObjectField(TEXT("identity"), Identity) ||
        !Payload->TryGetObjectField(TEXT("current_causal_state"), Current) ||
        !(*Current)->TryGetObjectField(TEXT("spatial_topology"), Topology) ||
        !(*Topology)->TryGetObjectField(TEXT("sites"), Sites) ||
        !(*Topology)->TryGetObjectField(TEXT("routes"), Routes) ||
        !HasExactKeys(*Sites, {SiteA, SiteB}) || !HasExactKeys(*Routes, {RouteId}) ||
        !(*Routes)->TryGetObjectField(RouteId, Route) ||
        !HasExactKeys(*Route, {TEXT("access_state"), TEXT("endpoint_semantics"), TEXT("endpoint_site_ids")}) ||
        !(*Route)->TryGetArrayField(TEXT("endpoint_site_ids"), Endpoints) ||
        !ExactStringArray2(*Endpoints, SiteA, SiteB) ||
        !ExactString(*Route, TEXT("endpoint_semantics"), TEXT("unordered_pair_fixture_only")) ||
        !ExactString(*Route, TEXT("access_state"), bRefresh ? TEXT("blocked") : TEXT("available")))
    {
        OutReason = TEXT("canonical_payload_structure_mismatch");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("payload_parse_and_canonical_identity_verification"), TEXT("after"), OutReason))
    {
        return false;
    }

    const FString ExpectedSite = Binding.DomainRole == TEXT("domain_A") ? SiteA : SiteB;
    const FString ExpectedSiteSlot = Binding.DomainRole == TEXT("domain_A") ? TEXT("domain_A_site_slot_01") : TEXT("domain_B_site_slot_01");
    const FString ExpectedRouteSlot = Binding.DomainRole == TEXT("domain_A") ? TEXT("domain_A_route_slot_01") : TEXT("domain_B_route_slot_01");
    const FString ExpectedProjectionId = FString::Printf(TEXT("simultaneous_domain_%s_%s_0001"), *RoleToken, *HeadRole);

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("operation_receipt_verification"), TEXT("before"), OutReason))
    {
        return false;
    }
    TSharedPtr<FJsonObject> Receipt;
    if (!LoadStoredBytesNoFollow(FPaths::Combine(Directory, ReceiptName), ReceiptBytes) ||
        !ParseStoredObject(ReceiptBytes, Receipt) ||
        !HasExactKeys(Receipt, {TEXT("receipt_schema"), TEXT("operation"), TEXT("proof_scenario"), TEXT("domain_role"),
            TEXT("expected_operational_process_instance_id"), TEXT("expected_source_represented_hash"),
            TEXT("expected_target_represented_hash"), TEXT("canonical_payload_raw_sha256"),
            TEXT("expected_canonical_hash"), TEXT("projection_raw_sha256"), TEXT("expected_projection_id")}) ||
        !ExactString(Receipt, TEXT("receipt_schema"), TEXT("SimultaneousPhysicalDomainOperationReceipt.v1")) ||
        !ExactString(Receipt, TEXT("operation"), *Operation) || !ExactString(Receipt, TEXT("proof_scenario"), Scenario) ||
        !ExactString(Receipt, TEXT("domain_role"), *Binding.DomainRole) ||
        !(bRefresh ? ExactString(Receipt, TEXT("expected_operational_process_instance_id"), *Binding.OperationalProcessInstanceId) : ExactNull(Receipt, TEXT("expected_operational_process_instance_id"))) ||
        !(bRefresh ? ExactString(Receipt, TEXT("expected_source_represented_hash"), H0) : ExactNull(Receipt, TEXT("expected_source_represented_hash"))) ||
        !ExactString(Receipt, TEXT("expected_target_represented_hash"), *ExpectedHash) ||
        !ExactString(Receipt, TEXT("canonical_payload_raw_sha256"), *ExpectedRawPayload) ||
        !ExactString(Receipt, TEXT("expected_canonical_hash"), *ExpectedHash) ||
        !ExactString(Receipt, TEXT("expected_projection_id"), *ExpectedProjectionId))
    {
        OutReason = TEXT("operation_receipt_verification_failed");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("operation_receipt_verification"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("projection_verification"), TEXT("before"), OutReason))
    {
        return false;
    }
    TSharedPtr<FJsonObject> Projection;
    if (!LoadStoredBytesNoFollow(FPaths::Combine(Directory, ProjectionName), ProjectionBytes) ||
        !ParseStoredObject(ProjectionBytes, Projection))
    {
        OutReason = TEXT("projection_open_or_parse_failure");
        return false;
    }
    const TSharedPtr<FJsonObject>* SiteProjection = nullptr;
    const TSharedPtr<FJsonObject>* RouteProjection = nullptr;
    if (!HasExactKeys(Projection, {TEXT("projection_schema"), TEXT("projection_id"), TEXT("proof_scenario"), TEXT("domain_role"),
        TEXT("source_canonical_hash"), TEXT("allowed_site_projection"), TEXT("allowed_route_projection")}) ||
        !ExactString(Projection, TEXT("projection_schema"), TEXT("SimultaneousPhysicalDomainProjection.v1")) ||
        !ExactString(Projection, TEXT("projection_id"), *ExpectedProjectionId) ||
        !ExactString(Projection, TEXT("proof_scenario"), Scenario) ||
        !ExactString(Projection, TEXT("domain_role"), *Binding.DomainRole) ||
        !ExactString(Projection, TEXT("source_canonical_hash"), *ExpectedHash) ||
        !Projection->TryGetObjectField(TEXT("allowed_site_projection"), SiteProjection) ||
        !Projection->TryGetObjectField(TEXT("allowed_route_projection"), RouteProjection) ||
        !HasExactKeys(*SiteProjection, {TEXT("canonical_site_id"), TEXT("representation_slot")}) ||
        !HasExactKeys(*RouteProjection, {TEXT("canonical_route_id"), TEXT("representation_slot")}) ||
        !ExactString(*SiteProjection, TEXT("canonical_site_id"), *ExpectedSite) ||
        !ExactString(*SiteProjection, TEXT("representation_slot"), *ExpectedSiteSlot) ||
        !ExactString(*RouteProjection, TEXT("canonical_route_id"), RouteId) ||
        !ExactString(*RouteProjection, TEXT("representation_slot"), *ExpectedRouteSlot))
    {
        OutReason = TEXT("projection_matrix_mismatch");
        return false;
    }
    const FString ProjectionHash = Sha256Bytes(ProjectionBytes);
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("projection_verification"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("visible_command_bundle_cross_field_verification"), TEXT("before"), OutReason))
    {
        return false;
    }
    if (!ExactString(Receipt, TEXT("projection_raw_sha256"), *ProjectionHash) ||
        !ExactString(Receipt, TEXT("expected_projection_id"), *ExpectedProjectionId))
    {
        OutReason = TEXT("operation_receipt_or_cross_field_mismatch");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("visible_command_bundle_cross_field_verification"), TEXT("after"), OutReason))
    {
        return false;
    }

    OutTuple.Payload = Payload;
    OutTuple.Projection = Projection;
    OutTuple.OperationReceipt = Receipt;
    OutTuple.RawPayloadHash = ExpectedRawPayload;
    OutTuple.CanonicalHash = ExpectedHash;
    OutTuple.RawProjectionHash = ProjectionHash;
    OutTuple.HeadRole = HeadRole;
    return true;
}

bool ASimultaneousPhysicalDomainProofAdapter::BuildAuthoritativeCandidate(
    const TSharedPtr<FJsonObject>& Payload,
    const TSharedPtr<FJsonObject>& Projection,
    FSPDAuthoritativeRepresentation& OutRepresentation,
    FSPDInjectedFaultPlan* FaultPlan,
    FString& OutReason) const
{
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("H1_authoritative_fact_derivation"), TEXT("before"), OutReason))
    {
        return false;
    }
    const TSharedPtr<FJsonObject>* Current = nullptr;
    const TSharedPtr<FJsonObject>* Topology = nullptr;
    const TSharedPtr<FJsonObject>* Routes = nullptr;
    const TSharedPtr<FJsonObject>* Route = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Endpoints = nullptr;
    FString AccessState;
    if (!Payload.IsValid() ||
        !Payload->TryGetObjectField(TEXT("current_causal_state"), Current) ||
        !(*Current)->TryGetObjectField(TEXT("spatial_topology"), Topology) ||
        !(*Topology)->TryGetObjectField(TEXT("routes"), Routes) ||
        !(*Routes)->TryGetObjectField(RouteId, Route) ||
        !(*Route)->TryGetArrayField(TEXT("endpoint_site_ids"), Endpoints) ||
        !ExactStringArray2(*Endpoints, SiteA, SiteB) ||
        !(*Route)->TryGetStringField(TEXT("access_state"), AccessState))
    {
        OutReason = TEXT("H1_authoritative_fact_derivation_failed");
        return false;
    }
    const FString CanonicalPayload = CanonicalizeObject(Payload);
    OutRepresentation.RawPayloadHash = Sha256Utf8(CanonicalPayload + TEXT("\n"));
    OutRepresentation.CanonicalHash = Sha256Utf8(CanonicalPayload);
    OutRepresentation.RouteId = RouteId;
    OutRepresentation.Endpoint0 = SiteA;
    OutRepresentation.Endpoint1 = SiteB;
    OutRepresentation.AccessState = AccessState;
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("H1_authoritative_fact_derivation"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("projection_slot_binding"), TEXT("before"), OutReason))
    {
        return false;
    }
    const TSharedPtr<FJsonObject>* SiteProjection = nullptr;
    const TSharedPtr<FJsonObject>* RouteProjection = nullptr;
    if (!Projection.IsValid() ||
        !Projection->TryGetStringField(TEXT("domain_role"), OutRepresentation.DomainRole) ||
        !Projection->TryGetObjectField(TEXT("allowed_site_projection"), SiteProjection) ||
        !Projection->TryGetObjectField(TEXT("allowed_route_projection"), RouteProjection) ||
        !Projection->TryGetStringField(TEXT("projection_id"), OutRepresentation.ProjectionId) ||
        !(*SiteProjection)->TryGetStringField(TEXT("canonical_site_id"), OutRepresentation.SiteId) ||
        !(*SiteProjection)->TryGetStringField(TEXT("representation_slot"), OutRepresentation.SiteSlot) ||
        !(*RouteProjection)->TryGetStringField(TEXT("representation_slot"), OutRepresentation.RouteSlot))
    {
        OutReason = TEXT("projection_slot_binding_failed");
        return false;
    }
    OutRepresentation.RawProjectionHash = Sha256Utf8(CanonicalizeObject(Projection) + TEXT("\n"));
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("projection_slot_binding"), TEXT("after"), OutReason))
    {
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("private_candidate_validation"), TEXT("before"), OutReason))
    {
        return false;
    }

    TSharedPtr<FJsonObject> Representation = MakeShared<FJsonObject>();
    Representation->SetStringField(TEXT("representation_schema"), TEXT("SimultaneousPhysicalDomainAuthoritativeDerivedRepresentation.v1"));
    Representation->SetStringField(TEXT("proof_scenario"), Scenario);
    Representation->SetStringField(TEXT("domain_role"), OutRepresentation.DomainRole);
    Representation->SetStringField(TEXT("accepted_canonical_payload_raw_sha256"), OutRepresentation.RawPayloadHash);
    Representation->SetStringField(TEXT("accepted_canonical_hash"), OutRepresentation.CanonicalHash);
    Representation->SetStringField(TEXT("accepted_projection_raw_sha256"), OutRepresentation.RawProjectionHash);
    Representation->SetStringField(TEXT("accepted_projection_id"), OutRepresentation.ProjectionId);
    Representation->SetStringField(TEXT("materialized_canonical_site_id"), OutRepresentation.SiteId);
    Representation->SetStringField(TEXT("materialized_site_representation_slot"), OutRepresentation.SiteSlot);
    Representation->SetStringField(TEXT("materialized_canonical_route_id"), OutRepresentation.RouteId);
    Representation->SetStringField(TEXT("materialized_route_representation_slot"), OutRepresentation.RouteSlot);
    Representation->SetArrayField(TEXT("materialized_endpoint_site_ids"), {StringValue(SiteA), StringValue(SiteB)});
    Representation->SetStringField(TEXT("materialized_route_access_state"), OutRepresentation.AccessState);
    OutRepresentation.CanonicalJson = CanonicalizeObject(Representation);
    OutRepresentation.RawStoredSha256 = Sha256Utf8(OutRepresentation.CanonicalJson + TEXT("\n"));
    const FString ExpectedSite = OutRepresentation.DomainRole == TEXT("domain_A") ? SiteA : SiteB;
    const bool bExactKnownHead =
        (OutRepresentation.CanonicalHash == H0 && OutRepresentation.AccessState == TEXT("available")) ||
        (OutRepresentation.CanonicalHash == H1 && OutRepresentation.AccessState == TEXT("blocked"));
    if (OutRepresentation.SiteId != ExpectedSite || OutRepresentation.RouteId != RouteId ||
        (OutRepresentation.DomainRole != TEXT("domain_A") && OutRepresentation.DomainRole != TEXT("domain_B")) ||
        !bExactKnownHead)
    {
        OutReason = TEXT("private_candidate_validation_failed");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("refresh"), TEXT("private_candidate_validation"), TEXT("after"), OutReason))
    {
        return false;
    }
    return true;
}

bool ASimultaneousPhysicalDomainProofAdapter::PublishCandidate(
    const FSPDAuthoritativeRepresentation& Candidate,
    const FSPDImmutableProcessBinding& Binding,
    TSharedPtr<FJsonObject>& OutReceipt,
    FString& OutReason)
{
    ASimultaneousPhysicalDomainRepresentationActor* NewRepresentation =
        GetWorld()->SpawnActor<ASimultaneousPhysicalDomainRepresentationActor>();
    if (NewRepresentation == nullptr || !NewRepresentation->PublishRepresentation(
        Candidate.DomainRole, Candidate.SiteId, Candidate.SiteSlot, Candidate.RouteId,
        Candidate.RouteSlot, Candidate.AccessState))
    {
        if (NewRepresentation != nullptr) NewRepresentation->Destroy();
        OutReason = TEXT("private_candidate_publication_failed");
        return false;
    }

    ASimultaneousPhysicalDomainRepresentationActor* Prior = PublishedRepresentation;
    PublishedRepresentation = NewRepresentation;
    RepresentedCanonicalHash = Candidate.CanonicalHash;
    if (Prior != nullptr)
    {
        Prior->Tags.Reset();
        Prior->SetActorHiddenInGame(true);
        Prior->Destroy();
    }
    OutReceipt = BuildMaterializationReceipt(Candidate, Binding);
    return OutReceipt.IsValid();
}

TSharedPtr<FJsonObject> ASimultaneousPhysicalDomainProofAdapter::BuildMaterializationReceipt(
    const FSPDAuthoritativeRepresentation& Representation,
    const FSPDImmutableProcessBinding& Binding) const
{
    TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
    Receipt->SetStringField(TEXT("receipt_schema"), TEXT("SimultaneousPhysicalDomainMaterializationReceipt.v1"));
    Receipt->SetStringField(TEXT("proof_scenario"), Scenario);
    Receipt->SetStringField(TEXT("domain_role"), Representation.DomainRole);
    Receipt->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    Receipt->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
    Receipt->SetStringField(TEXT("accepted_canonical_payload_raw_sha256"), Representation.RawPayloadHash);
    Receipt->SetStringField(TEXT("accepted_canonical_hash"), Representation.CanonicalHash);
    Receipt->SetStringField(TEXT("accepted_projection_raw_sha256"), Representation.RawProjectionHash);
    Receipt->SetStringField(TEXT("accepted_projection_id"), Representation.ProjectionId);
    Receipt->SetStringField(TEXT("materialized_canonical_site_id"), Representation.SiteId);
    Receipt->SetStringField(TEXT("materialized_site_representation_slot"), Representation.SiteSlot);
    Receipt->SetStringField(TEXT("materialized_canonical_route_id"), Representation.RouteId);
    Receipt->SetStringField(TEXT("materialized_route_representation_slot"), Representation.RouteSlot);
    Receipt->SetArrayField(TEXT("materialized_endpoint_site_ids"), {StringValue(SiteA), StringValue(SiteB)});
    Receipt->SetStringField(TEXT("materialized_route_access_state"), Representation.AccessState);
    Receipt->SetStringField(TEXT("authoritative_derived_representation_raw_sha256"), Representation.RawStoredSha256);
    Receipt->SetStringField(TEXT("receipt_authority"), TEXT("representation_only"));
    return Receipt;
}
