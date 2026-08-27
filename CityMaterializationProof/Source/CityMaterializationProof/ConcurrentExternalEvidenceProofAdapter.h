#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConcurrentExternalEvidenceProofAdapter.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

struct FConcurrentEvidenceMaterializationRecord
{
    FString CanonicalHash;
    FString RawPayloadHash;
    FString OutputDirectory;
    FString InteractionOpportunity;
    FString ProcessInstanceId;
    FString SourceDomain;
    FString PhysicalActorId;
};

// Exact materialization endpoint for Concurrent External Evidence Arbitration
// v0.1.0. It validates the frozen R0 and detached receipt, materializes one
// domain-local surface, and owns no ordering or canonical mutation authority.
UCLASS()
class CITYMATERIALIZATIONPROOF_API AConcurrentExternalEvidenceProofAdapter : public AActor
{
    GENERATED_BODY()

public:
    AConcurrentExternalEvidenceProofAdapter();

protected:
    virtual void BeginPlay() override;

private:
    bool LoadAndVerify(FConcurrentEvidenceMaterializationRecord& OutRecord, FString& OutFailure) const;
    void Materialize(const FConcurrentEvidenceMaterializationRecord& Record);
    void EmitAcceptanceReceipt(const FConcurrentEvidenceMaterializationRecord& Record) const;
    UStaticMeshComponent* AddBlock(const FVector& Location, const FVector& Scale, const FLinearColor& Color, bool bBlocksMovement);
    UTextRenderComponent* AddLabel(const FVector& Location, const FString& Text, const FColor& Color);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> ShapeMaterial;
};
