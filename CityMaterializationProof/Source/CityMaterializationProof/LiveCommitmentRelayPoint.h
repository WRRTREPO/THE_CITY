#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LiveCommitmentRelayPoint.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

// Fixture-local physical relay embodiment. It may write one evidenced proposal;
// Python remains the sole authority for commitments, claims, city records, and
// causal ledgers.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ALiveCommitmentRelayPoint : public AActor
{
    GENERATED_BODY()

public:
    ALiveCommitmentRelayPoint();

    void Configure(const FString& InSourceRecordHash, const FString& InExchangeDirectory, const FString& InClaimState, bool bRelayInitiallyActive);
    bool TryDisableByCrew(const FString& CrewId);

private:
    UStaticMeshComponent* AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bBlocksPawn);
    UTextRenderComponent* AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color);
    void BuildInteractable();
    void BuildDisabled();
    bool WritePhysicalProposal(const FString& CrewId) const;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> ShapeMaterial;

    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> InteractableConsole;

    UPROPERTY()
    TObjectPtr<UTextRenderComponent> InteractableLabel;

    FString SourceRecordHash;
    FString ExchangeDirectory;
    FString ClaimState;
    bool bRelayActive = false;
    bool bProposalEmitted = false;
};
