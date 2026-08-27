#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntegratedGateTokenPoint.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

// Fixture-local physical representation. It can only change its own disposable
// scene and emit the frozen Q envelope. Canonical validation remains Python.
UCLASS()
class CITYMATERIALIZATIONPROOF_API AIntegratedGateTokenPoint : public AActor
{
    GENERATED_BODY()

public:
    AIntegratedGateTokenPoint();

    void Configure(
        const FString& InCanonicalHash,
        const FString& InRawPayloadHash,
        const FString& InOutputDirectory,
        const FString& InInteractionOpportunity,
        bool bInitiallyEnabled,
        bool bInProposalCapabilityEnabled);
    bool TryDisableByCrew(const FString& CrewId);

private:
    UStaticMeshComponent* AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bInteractable);
    UTextRenderComponent* AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color);
    void BuildEnabled();
    void BuildDisabled();
    bool WriteExactQ(const FString& CrewId) const;

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
    bool bEnabled = false;
    bool bProposalCapabilityEnabled = false;
    bool bProposalEmitted = false;
};
