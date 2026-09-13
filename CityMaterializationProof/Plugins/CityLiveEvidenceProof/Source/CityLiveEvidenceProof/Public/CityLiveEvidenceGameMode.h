#pragma once

#include "CoreMinimal.h"
#include "Containers/Queue.h"
#include "GameFramework/GameModeBase.h"
#include "HAL/Runnable.h"
#include "CityLiveEvidenceGameMode.generated.h"

class FJsonObject;
class FLCERInputThread;
class FRunnableThread;
class ACityLiveEvidenceHeadAnchor;
class ACityLiveEvidenceResource;

UCLASS()
class CITYLIVEEVIDENCEPROOF_API ACityLiveEvidenceGameMode final : public AGameModeBase
{
    GENERATED_BODY()

public:
    ACityLiveEvidenceGameMode();
    virtual ~ACityLiveEvidenceGameMode() override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void RestartPlayer(AController* NewPlayer) override;
    void EnqueueInput(FString Line);

private:
    friend class FLCERInputThread;
    bool Startup();
    void Dispatch(const FString& Line);
    bool Bind(const TSharedPtr<FJsonObject>& Command, TSharedPtr<FJsonObject>& Result, FString& Error);
    bool AuthenticateMaterialize(const TSharedPtr<FJsonObject>& Command, FString& Raw, int32& Generation, FString& Error);
    void Materialize(const TSharedPtr<FJsonObject>& Command);
    void ContinueMaterialization();
    bool ArmFault(const TSharedPtr<FJsonObject>& Command, TSharedPtr<FJsonObject>& Result, FString& Error);
    bool FaultReady(const FString& Stage) const;
    bool ConsumeFault(const FString& Stage, const TSharedPtr<FJsonObject>& Before, const TSharedPtr<FJsonObject>& After);
    TSharedPtr<FJsonObject> Observe(const FString& Operation) const;
    TSharedPtr<FJsonObject> Routing(const FString& Operation) const;
    void Respond(const TSharedPtr<FJsonObject>& Command, const TSharedPtr<FJsonObject>& Payload, const FString& Error);
    void Send(const TSharedPtr<FJsonObject>& Object);
    void Fail(const FString& Error);

    TQueue<FString, EQueueMode::Mpsc> Input;
    TUniquePtr<FRunnable> InputWorker;
    FRunnableThread* InputThread = nullptr;
    TSharedPtr<FJsonObject> StartupRecord;
    TSharedPtr<FJsonObject> Binding;
    TSharedPtr<FJsonObject> PendingCommand;
    TSharedPtr<FJsonObject> ArmedFault;
    TArray<FString> Operations;
    FString Domain;
    FString Witness;
    FString Launch;
    FString RuntimeRoot;
    FString BindingHash;
    FString CurrentRaw;
    FString PendingRaw;
    FString R0Raw;
    int32 CurrentGeneration = -1;
    int32 PendingGeneration = -1;
    bool bStartupSent = false;
    bool bBound = false;
    bool bEmitted = false;
    bool bTerminal = false;
    bool bFaultConsumed = false;
    bool bAwaitingDestruction = false;

    UPROPERTY()
    TObjectPtr<ACityLiveEvidenceHeadAnchor> Anchor;
    UPROPERTY()
    TObjectPtr<ACityLiveEvidenceResource> Resource;
};
