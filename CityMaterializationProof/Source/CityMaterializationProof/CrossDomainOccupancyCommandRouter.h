#pragma once

#include "CoreMinimal.h"
#include "Containers/Queue.h"
#include "Containers/Ticker.h"

class FCrossDomainOccupancyProofAdapter;
class FCrossDomainOccupancyLiveWorldProbe;
class FCDOInputRunnable;
class FRunnableThread;
class FJsonObject;
class FJsonValue;
class UWorld;

struct FCDOImmutableProcessBinding
{
    FString DomainRole;
    FString WitnessId;
    FString HarnessLaunchId;
    FString ProcessRootRealpath;
    FString OperationalProcessInstanceId;
    FString ProcessBindingRawSha256;
    int32 Pid = 0;
    TSharedPtr<FJsonObject> CompleteBinding;
};

struct FCDOInjectedFaultPlan
{
    FString FaultOccurrenceId;
    FString CaseId;
    FString StageId;
    FString Edge;
    FString ArmedOperationId;
    bool bArmed = false;
    bool bInjected = false;
};

struct FCDOCommandContext
{
    int32 CommandSequence = 0;
    FString CommandSchema;
    FString CommandRawSha256;
    FString OperationId;
};

namespace CrossDomainOccupancyJson
{
    CITYMATERIALIZATIONPROOF_API bool ParseCanonicalObject(const FString& Canonical, TSharedPtr<FJsonObject>& OutObject);
    CITYMATERIALIZATIONPROOF_API FString CanonicalizeObject(const TSharedPtr<FJsonObject>& Object);
    CITYMATERIALIZATIONPROOF_API FString CanonicalizeValue(const TSharedPtr<FJsonValue>& Value);
    CITYMATERIALIZATIONPROOF_API FString Sha256Utf8(const FString& Value);
    CITYMATERIALIZATIONPROOF_API FString Sha256Bytes(const TArray<uint8>& Bytes);
    CITYMATERIALIZATIONPROOF_API bool HasExactKeys(const TSharedPtr<FJsonObject>& Object, std::initializer_list<const TCHAR*> Keys);
    CITYMATERIALIZATIONPROOF_API bool ExactString(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, const TCHAR* Expected);
    CITYMATERIALIZATIONPROOF_API bool IsLowerSha256(const FString& Value);
    CITYMATERIALIZATIONPROOF_API void EmitStructuredObject(const TSharedPtr<FJsonObject>& Object);
}

namespace CrossDomainOccupancyRuntime
{
    CITYMATERIALIZATIONPROOF_API void Initialize(const FCDOImmutableProcessBinding& Binding);
    CITYMATERIALIZATIONPROOF_API void BeginCommand(const FCDOCommandContext& Context);
    CITYMATERIALIZATIONPROOF_API void EmitStage(
        const FString& StageId,
        const FString& StageEdge,
        const FString& PublicationGeneration,
        const FString& RepresentedCanonicalHash,
        const TArray<TSharedPtr<FJsonValue>>& InputRows = {},
        const TSharedPtr<FJsonObject>& OutputIdentity = nullptr);
    CITYMATERIALIZATIONPROOF_API bool InjectAt(
        FCDOInjectedFaultPlan* Plan,
        const FString& StageId,
        const FString& Edge,
        FString& OutReason);
}

// Non-UObject, non-Actor router.  It is retained for the process lifetime by
// the bounded GameMode branch and is absent from every live Actor census.
class CITYMATERIALIZATIONPROOF_API FCrossDomainOccupancyCommandRouter final
{
public:
    FCrossDomainOccupancyCommandRouter();
    ~FCrossDomainOccupancyCommandRouter();

    bool Start(UWorld* InWorld);

private:
    bool Pump(float DeltaSeconds);
    void HandleLine(const FString& CanonicalLine);
    bool AcceptBinding(const TSharedPtr<FJsonObject>& Command, FString& OutReason);
    bool VerifyObservableBinding(
        const TSharedPtr<FJsonObject>& Binding,
        TSharedPtr<FJsonObject>& OutRuntimeProvenance,
        FString& OutReason) const;
    bool AcceptFaultArm(const TSharedPtr<FJsonObject>& Command, FString& OutReason);
    void EmitFailure(const FString& StageId, const FString& ReasonCode) const;
    void EmitBindReceipt() const;
    void EmitFaultArmReceipt() const;

    TWeakObjectPtr<UWorld> World;
    TQueue<FString, EQueueMode::Mpsc> PendingLines;
    FCDOInputRunnable* InputRunnable = nullptr;
    FRunnableThread* InputThread = nullptr;
    FTSTicker::FDelegateHandle TickerHandle;
    FCDOImmutableProcessBinding Binding;
    TUniquePtr<FCrossDomainOccupancyProofAdapter> Adapter;
    TUniquePtr<FCrossDomainOccupancyLiveWorldProbe> Probe;
    FCDOInjectedFaultPlan FaultPlan;
    int32 LastCommandSequence = 0;
    bool bBindingAccepted = false;
    bool bFaultArmAccepted = false;
    bool bTerminalLocalInvalid = false;
    bool bProtocolFailed = false;
};
