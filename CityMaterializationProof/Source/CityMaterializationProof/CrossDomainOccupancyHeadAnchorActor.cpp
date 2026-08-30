#include "CrossDomainOccupancyHeadAnchorActor.h"

#include "Dom/JsonObject.h"

namespace
{
constexpr TCHAR Scenario[] = TEXT("cross-domain-canonical-occupancy-materialization-v1");
constexpr TCHAR Occupant[] = TEXT("topology_occupant_0001");

bool IsLowerSha256(const FString& Value)
{
    if (Value.Len() != 64) return false;
    for (const TCHAR Character : Value)
    {
        if (!((Character >= '0' && Character <= '9') || (Character >= 'a' && Character <= 'f'))) return false;
    }
    return true;
}

TArray<TSharedPtr<FJsonValue>> SortedTags(const AActor& Actor)
{
    TArray<FString> Values;
    for (const FName Tag : Actor.Tags) Values.Add(Tag.ToString());
    Values.Sort();
    TArray<TSharedPtr<FJsonValue>> Result;
    for (const FString& Value : Values) Result.Add(MakeShared<FJsonValueString>(Value));
    return Result;
}
}

ACrossDomainOccupancyHeadAnchorActor::ACrossDomainOccupancyHeadAnchorActor()
{
    PrimaryActorTick.bCanEverTick = false;
    AutoReceiveInput = EAutoReceiveInput::Disabled;
    AnchorSchema = TEXT("CrossDomainOccupancyHeadAnchor.v1");
    ProofScenario = Scenario;
    CanonicalOccupantId = Occupant;
    RepresentationPublicationState = TEXT("locally_published_unverified");
}

bool ACrossDomainOccupancyHeadAnchorActor::ConfigureExact(
    const FString& InDomainRole,
    const FString& InOperationalProcessInstanceId,
    const FString& InProcessBindingRawSha256,
    const FString& InCanonicalPayloadRawSha256,
    const FString& InCanonicalHash,
    const FString& InProjectionRawSha256,
    const FString& InProjectionId,
    const FString& InProjectedSiteId,
    const FString& InSiteSlot,
    const FString& InSubjectSlot,
    const FString& InOccupancyKind,
    const FString& InOccupancyReference,
    const FString& InLocalDisposition,
    const FString& InPublicationGeneration)
{
    const bool bRoleA = InDomainRole == TEXT("domain_A");
    const bool bRoleB = InDomainRole == TEXT("domain_B");
    const bool bRoleFields = (bRoleA && InProjectedSiteId == TEXT("topology_site_0001") &&
        InSiteSlot == TEXT("domain_A_site_slot_01") && InSubjectSlot == TEXT("domain_A_subject_slot_01")) ||
        (bRoleB && InProjectedSiteId == TEXT("topology_site_0002") &&
        InSiteSlot == TEXT("domain_B_site_slot_01") && InSubjectSlot == TEXT("domain_B_subject_slot_01"));
    const bool bDisposition = InLocalDisposition == TEXT("present_at_local_site") ||
        InLocalDisposition == TEXT("remote_at_other_site") ||
        InLocalDisposition == TEXT("in_transition_out_of_domain");
    const bool bKind = InOccupancyKind == TEXT("at_site") || InOccupancyKind == TEXT("in_transition");
    const bool bGeneration = InPublicationGeneration == TEXT("publication_0001") ||
        InPublicationGeneration == TEXT("publication_0002") || InPublicationGeneration == TEXT("publication_0003");
    if (!bRoleFields || !bDisposition || !bKind || !bGeneration ||
        !IsLowerSha256(InOperationalProcessInstanceId) || !IsLowerSha256(InProcessBindingRawSha256) ||
        !IsLowerSha256(InCanonicalPayloadRawSha256) || !IsLowerSha256(InCanonicalHash) ||
        !IsLowerSha256(InProjectionRawSha256) || InProjectionId.IsEmpty() || InOccupancyReference.IsEmpty())
    {
        return false;
    }

    DomainRole = InDomainRole;
    OperationalProcessInstanceId = InOperationalProcessInstanceId;
    ProcessBindingRawSha256 = InProcessBindingRawSha256;
    AcceptedCanonicalPayloadRawSha256 = InCanonicalPayloadRawSha256;
    AcceptedCanonicalHash = InCanonicalHash;
    AcceptedProjectionRawSha256 = InProjectionRawSha256;
    AcceptedProjectionId = InProjectionId;
    ProjectedCanonicalSiteId = InProjectedSiteId;
    ProjectedSiteRepresentationSlot = InSiteSlot;
    ProjectedSubjectRepresentationSlot = InSubjectSlot;
    CanonicalOccupancyKind = InOccupancyKind;
    CanonicalOccupancyReference = InOccupancyReference;
    LocalSubjectDisposition = InLocalDisposition;
    PublicationGeneration = InPublicationGeneration;
    Tags.Reset();
    Tags.Add(FName(*FString::Printf(TEXT("cross_domain_occupancy/%s/head_anchor"), *DomainRole)));
    return true;
}

TSharedPtr<FJsonObject> ACrossDomainOccupancyHeadAnchorActor::BuildLiveFieldRow() const
{
    TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
    Row->SetStringField(TEXT("accepted_canonical_hash"), AcceptedCanonicalHash);
    Row->SetStringField(TEXT("accepted_canonical_payload_raw_sha256"), AcceptedCanonicalPayloadRawSha256);
    Row->SetStringField(TEXT("accepted_projection_id"), AcceptedProjectionId);
    Row->SetStringField(TEXT("accepted_projection_raw_sha256"), AcceptedProjectionRawSha256);
    Row->SetStringField(TEXT("actor_class"), GetClass()->GetPathName());
    Row->SetBoolField(TEXT("actor_has_begun_play"), HasActorBegunPlay());
    Row->SetBoolField(TEXT("actor_hidden"), IsHidden());
    Row->SetBoolField(TEXT("actor_is_being_destroyed"), IsActorBeingDestroyed());
    Row->SetBoolField(TEXT("actor_object_destroy_flags"), HasAnyFlags(RF_BeginDestroyed | RF_FinishDestroyed));
    Row->SetStringField(TEXT("actor_path"), GetPathName());
    Row->SetArrayField(TEXT("actor_tags"), SortedTags(*this));
    Row->SetStringField(TEXT("anchor_schema"), AnchorSchema);
    Row->SetStringField(TEXT("canonical_occupancy_kind"), CanonicalOccupancyKind);
    Row->SetStringField(TEXT("canonical_occupancy_reference"), CanonicalOccupancyReference);
    Row->SetStringField(TEXT("canonical_occupant_id"), CanonicalOccupantId);
    Row->SetStringField(TEXT("domain_role"), DomainRole);
    Row->SetStringField(TEXT("local_subject_disposition"), LocalSubjectDisposition);
    Row->SetStringField(TEXT("operational_process_instance_id"), OperationalProcessInstanceId);
    Row->SetStringField(TEXT("process_binding_raw_sha256"), ProcessBindingRawSha256);
    Row->SetStringField(TEXT("projected_canonical_site_id"), ProjectedCanonicalSiteId);
    Row->SetStringField(TEXT("projected_site_representation_slot"), ProjectedSiteRepresentationSlot);
    Row->SetStringField(TEXT("projected_subject_representation_slot"), ProjectedSubjectRepresentationSlot);
    Row->SetStringField(TEXT("proof_scenario"), ProofScenario);
    Row->SetStringField(TEXT("publication_generation"), PublicationGeneration);
    Row->SetStringField(TEXT("representation_publication_state"), RepresentationPublicationState);
    return Row;
}
