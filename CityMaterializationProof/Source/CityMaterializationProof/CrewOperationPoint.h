#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CrewOperationPoint.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

// A local first-person operation surface.  It may emit one evidenced proposal;
// the canonical Python transaction layer remains sole authority for persistence.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ACrewOperationPoint : public AActor
{
    GENERATED_BODY()

public:
    ACrewOperationPoint();

    void Configure(const FString& InSourceRecordHash, const FString& InExchangeDirectory, const FString& InOperationDomain, bool bInitiallyResolved);
    bool TryResolveByCrew(const FString& CrewId);

private:
    UStaticMeshComponent* AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bBlocksPawn);
    UTextRenderComponent* AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color);
    void BuildInteractable();
    void BuildResolved();
    bool WritePhysicalProposal(const FString& CrewId) const;
    bool IsFireControl() const;

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
    FString OperationDomain;
    bool bResolved = false;
};
