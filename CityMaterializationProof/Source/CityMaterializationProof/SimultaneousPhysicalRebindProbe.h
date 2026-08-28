#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SimultaneousPhysicalDomainCommandRouter.h"
#include "SimultaneousPhysicalRebindProbe.generated.h"

class FJsonObject;

// Receipt-independent observer.  It sees only the immutable process binding,
// the inspection label, and live Actor/component surfaces in the UE world.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ASimultaneousPhysicalRebindProbe : public AActor
{
    GENERATED_BODY()

public:
    ASimultaneousPhysicalRebindProbe();

    bool BindProcessIdentity(const FSPDImmutableProcessBinding& Binding);
    bool InspectPublishedRoute(
        const FString& InspectionId,
        TSharedPtr<FJsonObject>& OutObservation,
        FString& OutReason) const;

private:
    FString DomainRole;
    FString OperationalProcessInstanceId;
    FString ProcessBindingRawSha256;
    FString ProbeTag;
    bool bBound = false;
};
