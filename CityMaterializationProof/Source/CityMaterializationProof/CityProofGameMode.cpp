#include "CityProofGameMode.h"

#include "CityMaterializationActor.h"
#include "CityProofCharacter.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

ACityProofGameMode::ACityProofGameMode()
{
    DefaultPawnClass = ACityProofCharacter::StaticClass();
}

void ACityProofGameMode::BeginPlay()
{
    Super::BeginPlay();

    GetWorld()->SpawnActor<ACityMaterializationActor>(ACityMaterializationActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);

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
