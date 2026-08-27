#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntegratedUnrealProofAdapter.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

struct FIntegratedUnrealMaterializationRecord
{
    FString CanonicalHash;
    FString RawPayloadHash;
    FString GateState;
    FString AlphaState;
    FString OutputDirectory;
    FString InteractionOpportunity;
    FString ProcessInstanceId;
    bool bProposalCapabilityEnabled = false;
};

// The adapter is a representation-only endpoint. It reads the two detached
// proof-input files, validates them, materializes the fixture, and emits only
// operational receipts or Q. It owns no canonical execution behavior.
UCLASS()
class CITYMATERIALIZATIONPROOF_API AIntegratedUnrealProofAdapter : public AActor
{
    GENERATED_BODY()

public:
    AIntegratedUnrealProofAdapter();

protected:
    virtual void BeginPlay() override;

private:
    bool LoadAndVerify(FIntegratedUnrealMaterializationRecord& OutRecord, FString& OutFailure) const;
    void Materialize(const FIntegratedUnrealMaterializationRecord& Record);
    void EmitAcceptanceReceipt(const FIntegratedUnrealMaterializationRecord& Record) const;
    UStaticMeshComponent* AddBlock(const FVector& Location, const FVector& Scale, const FLinearColor& Color, bool bBlocksMovement);
    UTextRenderComponent* AddLabel(const FVector& Location, const FString& Text, const FColor& Color);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> ShapeMaterial;
};
