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
        TSharedPtr<FJsonObject>& OutReceipt,
        FString& OutReason);

    const FString& GetRepresentedCanonicalHash() const { return RepresentedCanonicalHash; }

private:
    bool LoadVisibleTuple(
        const FSPDImmutableProcessBinding& Binding,
        bool bRefresh,
        FSPDAuthoritativeRepresentation& OutRepresentation,
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
};
