#pragma once

#include "CoreMinimal.h"
#include "Containers/Queue.h"
#include "GameFramework/Actor.h"
#include "SimultaneousPhysicalDomainCommandRouter.generated.h"

class ASimultaneousPhysicalDomainProofAdapter;
class ASimultaneousPhysicalRebindProbe;
class FRunnableThread;
class FSPDInputRunnable;
class FJsonObject;
class FJsonValue;

struct FSPDImmutableProcessBinding
{
    FString DomainRole;
    FString WitnessId;
    FString ProcessRootRealpath;
    FString OperationalProcessInstanceId;
    FString ProcessBindingRawSha256;
    int32 Pid = 0;
    TSharedPtr<FJsonObject> CompleteBinding;
};

// Shared proof-local JSON/byte helpers.  They carry no canonical resolver,
// guard, head observer, refresh eligibility, or expected physical state.
namespace SimultaneousPhysicalDomainJson
{
    CITYMATERIALIZATIONPROOF_API bool ParseCanonicalObject(const FString& Canonical, TSharedPtr<FJsonObject>& OutObject);
    CITYMATERIALIZATIONPROOF_API FString CanonicalizeObject(const TSharedPtr<FJsonObject>& Object);
    CITYMATERIALIZATIONPROOF_API FString CanonicalizeValue(const TSharedPtr<FJsonValue>& Value);
    CITYMATERIALIZATIONPROOF_API FString Sha256Utf8(const FString& Value);
    CITYMATERIALIZATIONPROOF_API FString Sha256Bytes(const TArray<uint8>& Bytes);
    CITYMATERIALIZATIONPROOF_API bool LoadExactStoredJsonNoFollow(const FString& Path, TArray<uint8>& OutBytes, TSharedPtr<FJsonObject>& OutObject);
    CITYMATERIALIZATIONPROOF_API bool HasExactKeys(const TSharedPtr<FJsonObject>& Object, std::initializer_list<const TCHAR*> Keys);
    CITYMATERIALIZATIONPROOF_API bool ExactString(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, const TCHAR* Expected);
    CITYMATERIALIZATIONPROOF_API bool IsLowerSha256(const FString& Value);
    CITYMATERIALIZATIONPROOF_API void EmitStructuredObject(const TSharedPtr<FJsonObject>& Object);
}

// The one proof-local stdin router.  It accepts a process binding once, then
// exactly two independent inspection commands and one refresh command.  It
// never receives harness head observation or physical guard state.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ASimultaneousPhysicalDomainCommandRouter : public AActor
{
    GENERATED_BODY()

public:
    ASimultaneousPhysicalDomainCommandRouter();

protected:
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    bool AcceptBinding(const TSharedPtr<FJsonObject>& Command, FString& OutReason);
    bool VerifyObservableBinding(const TSharedPtr<FJsonObject>& Binding, FString& OutReason) const;
    void HandleLine(const FString& CanonicalLine);
    void EmitFailure(const FString& PublicationStage, const FString& ReasonCode) const;

    TQueue<FString, EQueueMode::Mpsc> PendingLines;
    FSPDInputRunnable* InputRunnable = nullptr;
    FRunnableThread* InputThread = nullptr;
    FSPDImmutableProcessBinding ImmutableBinding;
    bool bBindingAccepted = false;
    bool bLaunchInspectionAccepted = false;
    bool bRefreshAccepted = false;
    bool bRefreshInspectionAccepted = false;
    bool bProtocolFailed = false;

    UPROPERTY()
    TObjectPtr<ASimultaneousPhysicalDomainProofAdapter> Adapter;

    UPROPERTY()
    TObjectPtr<ASimultaneousPhysicalRebindProbe> Probe;
};
