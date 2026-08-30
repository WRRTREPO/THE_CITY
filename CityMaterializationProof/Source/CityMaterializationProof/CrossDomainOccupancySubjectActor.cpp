#include "CrossDomainOccupancySubjectActor.h"

#include "Dom/JsonObject.h"

namespace
{
constexpr TCHAR Scenario[] = TEXT("cross-domain-canonical-occupancy-materialization-v1");

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

ACrossDomainOccupancySubjectActor::ACrossDomainOccupancySubjectActor()
{
    PrimaryActorTick.bCanEverTick = false;
    AutoReceiveInput = EAutoReceiveInput::Disabled;
    SubjectSchema = TEXT("CrossDomainOccupancySubjectRepresentation.v1");
    ProofScenario = Scenario;
    CanonicalOccupantId = TEXT("topology_occupant_0001");
    RepresentationPublicationState = TEXT("locally_published_unverified");
}

bool ACrossDomainOccupancySubjectActor::ConfigureExact(
    const FString& InDomainRole,
    const FString& InOperationalProcessInstanceId,
    const FString& InProcessBindingRawSha256,
    const FString& InCanonicalPayloadRawSha256,
    const FString& InCanonicalHash,
    const FString& InProjectionRawSha256,
    const FString& InProjectionId,
    const FString& InRepresentedSiteId,
    const FString& InSubjectSlot,
    const FString& InPublicationGeneration)
{
    const bool bRoleFields =
        (InDomainRole == TEXT("domain_A") && InRepresentedSiteId == TEXT("topology_site_0001") &&
            InSubjectSlot == TEXT("domain_A_subject_slot_01")) ||
        (InDomainRole == TEXT("domain_B") && InRepresentedSiteId == TEXT("topology_site_0002") &&
            InSubjectSlot == TEXT("domain_B_subject_slot_01"));
    const bool bGeneration = InPublicationGeneration == TEXT("publication_0001") ||
        InPublicationGeneration == TEXT("publication_0003");
    if (!bRoleFields || !bGeneration || !IsLowerSha256(InOperationalProcessInstanceId) ||
        !IsLowerSha256(InProcessBindingRawSha256) || !IsLowerSha256(InCanonicalPayloadRawSha256) ||
        !IsLowerSha256(InCanonicalHash) || !IsLowerSha256(InProjectionRawSha256) || InProjectionId.IsEmpty())
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
    RepresentedSiteId = InRepresentedSiteId;
    SubjectRepresentationSlot = InSubjectSlot;
    PublicationGeneration = InPublicationGeneration;
    Tags.Reset();
    Tags.Add(FName(*FString::Printf(
        TEXT("cross_domain_occupancy/%s/%s"), *DomainRole, *SubjectRepresentationSlot)));
    return true;
}

TSharedPtr<FJsonObject> ACrossDomainOccupancySubjectActor::BuildLiveFieldRow() const
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
    Row->SetStringField(TEXT("canonical_occupant_id"), CanonicalOccupantId);
    Row->SetStringField(TEXT("domain_role"), DomainRole);
    Row->SetStringField(TEXT("operational_process_instance_id"), OperationalProcessInstanceId);
    Row->SetStringField(TEXT("process_binding_raw_sha256"), ProcessBindingRawSha256);
    Row->SetStringField(TEXT("proof_scenario"), ProofScenario);
    Row->SetStringField(TEXT("publication_generation"), PublicationGeneration);
    Row->SetStringField(TEXT("representation_publication_state"), RepresentationPublicationState);
    Row->SetStringField(TEXT("represented_site_id"), RepresentedSiteId);
    Row->SetStringField(TEXT("subject_representation_slot"), SubjectRepresentationSlot);
    Row->SetStringField(TEXT("subject_schema"), SubjectSchema);
    return Row;
}
