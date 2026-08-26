#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CityMaterializationActor.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;

USTRUCT()
struct FCityProofRecord
{
    GENERATED_BODY()

    FString RecordName;
    FString CanonicalHash;
    bool bBridgeOpen = false;
    int32 BridgeCapacity = 0;
    FString BridgeAccessPointState;
    bool bBridgeAccessRoundTripRecord = false;
    bool bBridgeAccessContentionRecord = false;
    int32 FireIntensity = 0;
    FString PoliceLocation;
    FString PoliceAvailability;
    int32 PolicePresentAtDocklands = 0;
    FString DocklandsOwner;
    int32 GangControl = 0;
    int32 RivalControl = 0;
};

UCLASS()
class CITYMATERIALIZATIONPROOF_API ACityMaterializationActor : public AActor
{
    GENERATED_BODY()

public:
    ACityMaterializationActor();

protected:
    virtual void BeginPlay() override;

private:
    bool LoadAuthoritativeRecord(FCityProofRecord& OutRecord, FString& OutFailure) const;
    void Materialize(const FCityProofRecord& Record);
    void SpawnBridgeAccessPoint(const FCityProofRecord& Record);
    UStaticMeshComponent* AddBlock(const FVector& Location, const FVector& Scale, const FLinearColor& Color, bool bBlocksMovement);
    UTextRenderComponent* AddLabel(const FVector& Location, const FString& Text, const FColor& Color);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> ShapeMaterial;
};
