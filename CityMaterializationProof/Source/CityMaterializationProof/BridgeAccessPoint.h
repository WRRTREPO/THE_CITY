#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BridgeAccessPoint.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

UCLASS()
class CITYMATERIALIZATIONPROOF_API ABridgeAccessPoint : public AActor
{
    GENERATED_BODY()

public:
    ABridgeAccessPoint();

    void Configure(const FString& InSourceRecordHash, const FString& InExchangeDirectory, bool bInitiallyDestroyed, bool bInContentionProof);
    bool TryDestroyByCrew(const FString& CrewId);

private:
    UStaticMeshComponent* AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bBlocksPawn);
    UTextRenderComponent* AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color);
    void BuildIntact();
    void BuildDestroyed();
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
    bool bContentionProof = false;
    bool bDestroyed = false;
};
