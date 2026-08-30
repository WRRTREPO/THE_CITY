#pragma once

#include "CoreMinimal.h"
#include "CrossDomainOccupancyCommandRouter.h"

class FJsonObject;
class UWorld;

// Retained non-UObject census oracle.  It receives no adapter, receipt,
// expectation, payload, projection, guard, or canonical-head pointer.
class CITYMATERIALIZATIONPROOF_API FCrossDomainOccupancyLiveWorldProbe final
{
public:
    FCrossDomainOccupancyLiveWorldProbe(UWorld* InWorld, const FCDOImmutableProcessBinding& InBinding);

    bool InspectOnce(
        const FString& InspectionId,
        FCDOInjectedFaultPlan* FaultPlan,
        TSharedPtr<FJsonObject>& OutObservation,
        FString& OutReason) const;

private:
    bool Stage(
        const FString& StageId,
        FCDOInjectedFaultPlan* FaultPlan,
        const TFunction<bool()>& Work,
        FString& OutReason,
        const TSharedPtr<FJsonObject>& OutputIdentity = nullptr) const;

    TWeakObjectPtr<UWorld> World;
    FString DomainRole;
    FString OperationalProcessInstanceId;
    FString ProcessBindingRawSha256;
};
