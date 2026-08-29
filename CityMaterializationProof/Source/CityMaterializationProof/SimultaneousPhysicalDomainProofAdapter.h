#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SimultaneousPhysicalDomainCommandRouter.h"
#include "SimultaneousPhysicalDomainProofAdapter.generated.h"

class ASimultaneousPhysicalDomainRepresentationActor;
class FJsonObject;

struct FSPDAuthoritativeRepresentation
{
    FString DomainRole;
    FString RawPayloadHash;
    FString CanonicalHash;
    FString RawProjectionHash;
    FString ProjectionId;
    FString SiteId;
    FString SiteSlot;
    FString RouteId;
    FString RouteSlot;
    FString Endpoint0;
    FString Endpoint1;
    FString AccessState;
    FString CanonicalJson;
    FString RawStoredSha256;
};

struct FSPDValidatedVisibleTuple
{
    TSharedPtr<FJsonObject> Payload;
    TSharedPtr<FJsonObject> Projection;
    TSharedPtr<FJsonObject> OperationReceipt;
    FString RawPayloadHash;
    FString CanonicalHash;
    FString RawProjectionHash;
    FString HeadRole;
};

// Exact two-input disposable representation constructor and atomic local
// publisher.  It receives no harness observation, guard, stale classification,
// current-head flag, other-domain state, or expected physical result.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ASimultaneousPhysicalDomainProofAdapter : public AActor
{
    GENERATED_BODY()

public:
    ASimultaneousPhysicalDomainProofAdapter();

    bool MaterializeLaunch(
        const FSPDImmutableProcessBinding& Binding,
        TSharedPtr<FJsonObject>& OutReceipt,
        FString& OutReason);

    bool RefreshOnce(
        const FSPDImmutableProcessBinding& Binding,
        FSPDInjectedFaultPlan* FaultPlan,
        TSharedPtr<FJsonObject>& OutReceipt,
        FString& OutReason);

    bool ExecuteNonconsequentialStepOnce(
        const FSPDImmutableProcessBinding& Binding,
        TSharedPtr<FJsonObject>& OutObservation,
        FString& OutReason);

    TSharedPtr<FJsonObject> BuildRetentionExecutionObservation(
        const FSPDImmutableProcessBinding& Binding) const;

    const FString& GetRepresentedCanonicalHash() const { return RepresentedCanonicalHash; }
    FString GetPublicationState() const;

private:
    bool LoadVisibleTuple(
        const FSPDImmutableProcessBinding& Binding,
        bool bRefresh,
        FSPDValidatedVisibleTuple& OutTuple,
        FSPDInjectedFaultPlan* FaultPlan,
        FString& OutReason) const;
    bool BuildAuthoritativeCandidate(
        const TSharedPtr<FJsonObject>& Payload,
        const TSharedPtr<FJsonObject>& Projection,
        FSPDAuthoritativeRepresentation& OutRepresentation,
        FSPDInjectedFaultPlan* FaultPlan,
        FString& OutReason) const;
    bool PublishCandidate(
        const FSPDAuthoritativeRepresentation& Candidate,
        const FSPDImmutableProcessBinding& Binding,
        TSharedPtr<FJsonObject>& OutReceipt,
        FString& OutReason);
    TSharedPtr<FJsonObject> BuildMaterializationReceipt(
        const FSPDAuthoritativeRepresentation& Representation,
        const FSPDImmutableProcessBinding& Binding) const;

    UPROPERTY()
    TObjectPtr<ASimultaneousPhysicalDomainRepresentationActor> PublishedRepresentation;

    FString RepresentedCanonicalHash;
    uint64 NonconsequentialTickCounter = 0;
    FString CosmeticPhaseToken;
    uint64 DiagnosticCounter = 0;
    bool bRefreshConsumed = false;
    bool bRetentionWitness = false;
    bool bPerturbedRetentionWitness = false;
    bool bPoisonObservedBeforeRefresh = false;
    bool bPublishedH1PoisonClear = false;
    bool bPriorH0ActorReplaced = false;
    bool bLocalStepConsumed = false;
};
