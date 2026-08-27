#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CanonicalSpatialTopologyProofAdapter.generated.h"

class ACanonicalTopologyRepresentationActor;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UTextRenderComponent;

struct FCanonicalTopologyMaterializationRecord
{
    FString CanonicalHash;
    FString RawPayloadHash;
    FString RawMapHash;
    FString MappingId;
    FString AccessState;
    FString CanonicalRouteId;
    FString EndpointSiteId0;
    FString EndpointSiteId1;
    FString ProcessInstanceId;
};

// Read-only projection endpoint for Canonical Spatial Topology Identity v0.1.0.
// It validates exactly three detached proof inputs and creates disposable local
// representation.  It exposes no evidence/Q, scheduler, resolver, ledger, or
// canonical-write path.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ACanonicalSpatialTopologyProofAdapter : public AActor
{
    GENERATED_BODY()

public:
    ACanonicalSpatialTopologyProofAdapter();

protected:
    virtual void BeginPlay() override;

private:
    bool LoadAndVerify(FCanonicalTopologyMaterializationRecord& OutRecord, FString& OutStage, FString& OutReason) const;
    bool Materialize(const FCanonicalTopologyMaterializationRecord& Record, FString& OutStage, FString& OutReason);
    void EmitMaterializationReceipt(const FCanonicalTopologyMaterializationRecord& Record) const;
    void EmitFailure(const FString& Stage, const FString& Reason) const;
    UStaticMeshComponent* AddLocalBlock(const FVector& Location, const FVector& Scale, const FLinearColor& Color);
    UTextRenderComponent* AddLocalLabel(const FVector& Location, const FString& Text, const FColor& Color);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> ShapeMaterial;

    UPROPERTY()
    TObjectPtr<ACanonicalTopologyRepresentationActor> SiteActor01;

    UPROPERTY()
    TObjectPtr<ACanonicalTopologyRepresentationActor> SiteActor02;

    UPROPERTY()
    TObjectPtr<ACanonicalTopologyRepresentationActor> RouteActor01;
};
