#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CrossDomainOccupancySubjectActor.generated.h"

class FJsonObject;

// Symbolic local-site correspondence for the sole canonical occupant.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ACrossDomainOccupancySubjectActor final : public AActor
{
    GENERATED_BODY()

public:
    ACrossDomainOccupancySubjectActor();

    bool ConfigureExact(
        const FString& InDomainRole,
        const FString& InOperationalProcessInstanceId,
        const FString& InProcessBindingRawSha256,
        const FString& InCanonicalPayloadRawSha256,
        const FString& InCanonicalHash,
        const FString& InProjectionRawSha256,
        const FString& InProjectionId,
        const FString& InRepresentedSiteId,
        const FString& InSubjectSlot,
        const FString& InPublicationGeneration);

    TSharedPtr<FJsonObject> BuildLiveFieldRow() const;
    const FString& GetPublicationGeneration() const { return PublicationGeneration; }

private:
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString SubjectSchema;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString ProofScenario;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString DomainRole;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString OperationalProcessInstanceId;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString ProcessBindingRawSha256;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString CanonicalOccupantId;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString RepresentedSiteId;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString SubjectRepresentationSlot;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AcceptedCanonicalPayloadRawSha256;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AcceptedCanonicalHash;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AcceptedProjectionRawSha256;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString AcceptedProjectionId;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString PublicationGeneration;
    UPROPERTY(VisibleAnywhere, Category="Phase4Proof") FString RepresentationPublicationState;
};
