#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CrossDomainOccupancyHeadAnchorActor.generated.h"

class FJsonObject;

// Disposable positive witness for one accepted local representation generation.
// It has no canonical, scheduling, completion, input, or peer capability.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ACrossDomainOccupancyHeadAnchorActor final : public AActor
{
    GENERATED_BODY()

public:
    ACrossDomainOccupancyHeadAnchorActor();

    bool ConfigureExact(
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
        const FString& InPublicationGeneration);

    TSharedPtr<FJsonObject> BuildLiveFieldRow() const;
    const FString& GetPublicationGeneration() const { return PublicationGeneration; }

private:
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AnchorSchema;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString ProofScenario;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString DomainRole;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString OperationalProcessInstanceId;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString ProcessBindingRawSha256;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AcceptedCanonicalPayloadRawSha256;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AcceptedCanonicalHash;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AcceptedProjectionRawSha256;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AcceptedProjectionId;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString ProjectedCanonicalSiteId;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString ProjectedSiteRepresentationSlot;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString ProjectedSubjectRepresentationSlot;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString CanonicalOccupantId;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString CanonicalOccupancyKind;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString CanonicalOccupancyReference;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString LocalSubjectDisposition;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString PublicationGeneration;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString RepresentationPublicationState;
};
