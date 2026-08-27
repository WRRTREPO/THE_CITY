#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CanonicalTopologyRepresentationActor.generated.h"

class UStaticMeshComponent;

// One disposable visual role in the canonical-topology proof.  This Actor has
// no canonical identity or mutation behavior; its process-local name is
// retained only in the detached materialization receipt.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ACanonicalTopologyRepresentationActor : public AActor
{
    GENERATED_BODY()

public:
    ACanonicalTopologyRepresentationActor();
    void Configure(const FVector& Scale, const FLinearColor& Color);

private:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Shape;
};
