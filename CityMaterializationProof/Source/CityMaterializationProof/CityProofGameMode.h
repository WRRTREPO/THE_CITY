#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "CityProofGameMode.generated.h"

UCLASS()
class CITYMATERIALIZATIONPROOF_API ACityProofGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ACityProofGameMode();

protected:
    virtual void BeginPlay() override;
};
