#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConcurrentEvidenceSurface.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

// Fixture-local physical evidence surface for the frozen concurrent external
// arbitration proof. It may change only its disposable representation and
// emit its preauthorized Q plus a detached operational receipt.
UCLASS()
class CITYMATERIALIZATIONPROOF_API AConcurrentEvidenceSurface : public AActor
{
    GENERATED_BODY()

public:
    AConcurrentEvidenceSurface();

    void Configure(
        const FString& InCanonicalHash,
        const FString& InRawPayloadHash,
        const FString& InOutputDirectory,
        const FString& InInteractionOpportunity,
        const FString& InProcessInstanceId,
        const FString& InSourceDomain);
    bool TryAllocateByCrew(const FString& CrewId);

private:
    UStaticMeshComponent* AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bInteractable);
    UTextRenderComponent* AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color);
    bool WriteExactEvidence();

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> ShapeMaterial;

    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> InteractionSurface;

    UPROPERTY()
    TObjectPtr<UTextRenderComponent> InteractionLabel;

    FString CanonicalHash;
    FString RawPayloadHash;
    FString OutputDirectory;
    FString InteractionOpportunity;
    FString ProcessInstanceId;
    FString SourceDomain;
    FString PhysicalActorId;
    FString InputId;
    FString PhysicalEventId;
    FString AllocationOwner;
    bool bEvidenceEmitted = false;
};
