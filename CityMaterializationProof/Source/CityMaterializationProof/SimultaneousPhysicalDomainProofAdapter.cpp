#include "SimultaneousPhysicalDomainProofAdapter.h"

#include "SimultaneousPhysicalDomainRepresentationActor.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"

#include <sys/stat.h>

namespace
{
using namespace SimultaneousPhysicalDomainJson;

constexpr TCHAR Scenario[] = TEXT("simultaneous-physical-domains-v1");
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
    return true;
}

TSharedPtr<FJsonValue> StringValue(const FString& Value)
{
    return MakeShared<FJsonValueString>(Value);
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
    FSPDAuthoritativeRepresentation Candidate;
    if (!LoadVisibleTuple(Binding, false, Candidate, OutReason))
    {
        return false;
    }
    if (Binding.WitnessId == TEXT("w5_retention_perturbed"))
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
    return PublishCandidate(Candidate, Binding, OutReceipt, OutReason);
}

bool ASimultaneousPhysicalDomainProofAdapter::RefreshOnce(
    const FSPDImmutableProcessBinding& Binding,
    TSharedPtr<FJsonObject>& OutReceipt,
    FString& OutReason)
{
    if (bRefreshConsumed || RepresentedCanonicalHash != H0 || PublishedRepresentation == nullptr)
    {
        OutReason = TEXT("refresh_not_exactly_once_from_H0");
        return false;
    }
    bRefreshConsumed = true;
    FSPDAuthoritativeRepresentation Candidate;
    if (!LoadVisibleTuple(Binding, true, Candidate, OutReason))
    {
        return false;
    }
    // The candidate above is a pure exact-H1-plus-projection reconstruction.
    // Only after it exists and validates are the three nonconsequential scalar
    // fields retained; none is an argument to LoadVisibleTuple.
    const uint64 RetainedTick = NonconsequentialTickCounter;
    const FString RetainedCosmetic = CosmeticPhaseToken;
    const uint64 RetainedDiagnostic = DiagnosticCounter;
    if (!PublishCandidate(Candidate, Binding, OutReceipt, OutReason))
    {
        return false;
    }
    NonconsequentialTickCounter = RetainedTick;
    CosmeticPhaseToken = RetainedCosmetic;
    DiagnosticCounter = RetainedDiagnostic;
    return true;
}

bool ASimultaneousPhysicalDomainProofAdapter::LoadVisibleTuple(
    const FSPDImmutableProcessBinding& Binding,
    bool bRefresh,
    FSPDAuthoritativeRepresentation& OutRepresentation,
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
    if (!StrictDirectory(Directory, {PayloadName, ProjectionName, ReceiptName}, OutReason))
    {
        return false;
    }

    TArray<uint8> PayloadBytes;
    TArray<uint8> ProjectionBytes;
    TArray<uint8> ReceiptBytes;
    TSharedPtr<FJsonObject> Payload;
    TSharedPtr<FJsonObject> Projection;
    TSharedPtr<FJsonObject> Receipt;
    if (!LoadExactStoredJsonNoFollow(FPaths::Combine(Directory, PayloadName), PayloadBytes, Payload) ||
        !LoadExactStoredJsonNoFollow(FPaths::Combine(Directory, ProjectionName), ProjectionBytes, Projection) ||
        !LoadExactStoredJsonNoFollow(FPaths::Combine(Directory, ReceiptName), ReceiptBytes, Receipt))
    {
        OutReason = TEXT("visible_input_open_parse_or_type_failure");
        return false;
    }
    const FString ExpectedRawPayload = bRefresh ? D1 : D0;
    const FString ExpectedHash = bRefresh ? H1 : H0;
    if (Sha256Bytes(PayloadBytes) != ExpectedRawPayload)
    {
        OutReason = TEXT("payload_raw_sha256_mismatch");
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

    const FString ExpectedSite = Binding.DomainRole == TEXT("domain_A") ? SiteA : SiteB;
    const FString ExpectedSiteSlot = Binding.DomainRole == TEXT("domain_A") ? TEXT("domain_A_site_slot_01") : TEXT("domain_B_site_slot_01");
    const FString ExpectedRouteSlot = Binding.DomainRole == TEXT("domain_A") ? TEXT("domain_A_route_slot_01") : TEXT("domain_B_route_slot_01");
    const FString ExpectedProjectionId = FString::Printf(TEXT("simultaneous_domain_%s_%s_0001"), *RoleToken, *HeadRole);
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

    if (!HasExactKeys(Receipt, {TEXT("receipt_schema"), TEXT("operation"), TEXT("proof_scenario"), TEXT("domain_role"),
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
        !ExactString(Receipt, TEXT("projection_raw_sha256"), *ProjectionHash) ||
        !ExactString(Receipt, TEXT("expected_projection_id"), *ExpectedProjectionId))
    {
        OutReason = TEXT("operation_receipt_or_cross_field_mismatch");
        return false;
    }

    OutRepresentation.DomainRole = Binding.DomainRole;
    OutRepresentation.RawPayloadHash = ExpectedRawPayload;
    OutRepresentation.CanonicalHash = ExpectedHash;
    OutRepresentation.RawProjectionHash = ProjectionHash;
    OutRepresentation.ProjectionId = ExpectedProjectionId;
    OutRepresentation.SiteId = ExpectedSite;
    OutRepresentation.SiteSlot = ExpectedSiteSlot;
    OutRepresentation.RouteId = RouteId;
    OutRepresentation.RouteSlot = ExpectedRouteSlot;
    OutRepresentation.Endpoint0 = SiteA;
    OutRepresentation.Endpoint1 = SiteB;
    OutRepresentation.AccessState = bRefresh ? TEXT("blocked") : TEXT("available");

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
