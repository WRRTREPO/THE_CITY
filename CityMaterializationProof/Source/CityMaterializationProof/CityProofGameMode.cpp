#include "CityProofGameMode.h"

#include "CityMaterializationActor.h"
#include "CityProofCharacter.h"
#include "CanonicalSpatialTopologyProofAdapter.h"
#include "ConcurrentExternalEvidenceProofAdapter.h"
#include "IntegratedUnrealProofAdapter.h"
#include "SimultaneousPhysicalDomainCommandRouter.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpectatorPawn.h"
#include "Misc/CommandLine.h"

ACityProofGameMode::ACityProofGameMode()
{
    // Topology proof worlds must never instantiate the legacy Q-capable pawn,
    // even transiently before BeginPlay replaces the view target.
    const FString CommandLine(FCommandLine::Get());
    DefaultPawnClass = CommandLine.Contains(TEXT("CanonicalTopologyProof"))
        ? ASpectatorPawn::StaticClass()
        : ACityProofCharacter::StaticClass();
}

void ACityProofGameMode::BeginPlay()
{
    Super::BeginPlay();

    FString IntegratedPayloadPath;
    FString ConcurrentPayloadPath;
    FString TopologyInputRoot;
    FParse::Value(FCommandLine::Get(), TEXT("IntegratedProofPayload="), IntegratedPayloadPath);
    FParse::Value(FCommandLine::Get(), TEXT("ConcurrentEvidencePayload="), ConcurrentPayloadPath);
    FParse::Value(FCommandLine::Get(), TEXT("CanonicalTopologyProofInputRoot="), TopologyInputRoot);
    // Any concurrent-proof selector enters the dedicated fail-closed adapter.
    // An incomplete selector set must never fall through to the legacy city
    // materializer and accidentally acquire a different representation path.
    const FString CommandLine(FCommandLine::Get());
    const bool bTopologyProofRequested = CommandLine.Contains(TEXT("CanonicalTopologyProof"));
    const bool bConcurrentProofRequested = CommandLine.Contains(TEXT("ConcurrentEvidence"));
    // Phase 3 deliberately has no truth-bearing argv selector.  Its frozen
    // launch surface is the only existing proof launch with -Multiprocess and
    // without a named topology, concurrent-evidence, or integrated payload.
    // The router still begins unbound and can acquire proof semantics only
    // from its one exact process-binding command on the original stdin pipe.
    const bool bSimultaneousPhysicalDomainProcess = CommandLine.Contains(TEXT("-Multiprocess")) &&
        !bTopologyProofRequested && !bConcurrentProofRequested && IntegratedPayloadPath.IsEmpty();
    if (bTopologyProofRequested)
    {
        GetWorld()->SpawnActor<ACanonicalSpatialTopologyProofAdapter>(ACanonicalSpatialTopologyProofAdapter::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    }
    else if (bConcurrentProofRequested)
    {
        GetWorld()->SpawnActor<AConcurrentExternalEvidenceProofAdapter>(AConcurrentExternalEvidenceProofAdapter::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    }
    else if (bSimultaneousPhysicalDomainProcess)
    {
        GetWorld()->SpawnActor<ASimultaneousPhysicalDomainCommandRouter>(ASimultaneousPhysicalDomainCommandRouter::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    }
    else if (IntegratedPayloadPath.IsEmpty())
    {
        GetWorld()->SpawnActor<ACityMaterializationActor>(ACityMaterializationActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    }
    else
    {
        GetWorld()->SpawnActor<AIntegratedUnrealProofAdapter>(AIntegratedUnrealProofAdapter::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    }

    APlayerController* Controller = GetWorld()->GetFirstPlayerController();
    if (Controller != nullptr)
    {
        if (APawn* ExistingPawn = Controller->GetPawn())
        {
            ExistingPawn->Destroy();
        }

        const FVector SpawnLocation(-700.0f, 250.0f, 110.0f);
        const FRotator SpawnRotation = (FVector(-120.0f, 250.0f, 110.0f) - SpawnLocation).Rotation();
        UClass* PawnClass = bTopologyProofRequested ? ASpectatorPawn::StaticClass() : DefaultPawnClass.Get();
        if (APawn* Pawn = GetWorld()->SpawnActor<APawn>(PawnClass, SpawnLocation, SpawnRotation))
        {
            Controller->Possess(Pawn);
            Controller->SetControlRotation(SpawnRotation);
            Controller->SetViewTarget(Pawn);
        }
    }
}
