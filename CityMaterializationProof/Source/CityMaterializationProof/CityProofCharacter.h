#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CityProofCharacter.generated.h"

class UCameraComponent;

UCLASS()
class CITYMATERIALIZATIONPROOF_API ACityProofCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ACityProofCharacter();

protected:
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

private:
    void MoveForward(float Value);
    void MoveRight(float Value);
    void AttemptBridgeAccessDestruction();

    UPROPERTY(VisibleAnywhere, Category = "Camera")
    TObjectPtr<UCameraComponent> FirstPersonCamera;
};
