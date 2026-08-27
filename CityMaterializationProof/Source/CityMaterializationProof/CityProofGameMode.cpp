#include "CityProofGameMode.h"

#include "CityMaterializationActor.h"
#include "CityProofCharacter.h"
#include "IntegratedUnrealProofAdapter.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"

ACityProofGameMode::ACityProofGameMode()
{
    DefaultPawnClass = ACityProofCharacter::StaticClass();
}

void ACityProofGameMode::BeginPlay()
{
    Super::BeginPlay();

    FString IntegratedPayloadPath;
    FParse::Value(FCommandLine::Get(), TEXT("IntegratedProofPayload="), IntegratedPayloadPath);
    if (IntegratedPayloadPath.IsEmpty())
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
        if (APawn* Pawn = GetWorld()->SpawnActor<APawn>(DefaultPawnClass, SpawnLocation, SpawnRotation))
        {
            Controller->Possess(Pawn);
            Controller->SetControlRotation(SpawnRotation);
            Controller->SetViewTarget(Pawn);
        }
    }
}
