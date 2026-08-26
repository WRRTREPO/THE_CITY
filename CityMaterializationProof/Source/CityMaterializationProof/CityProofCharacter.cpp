#include "CityProofCharacter.h"

#include "BridgeAccessPoint.h"
#include "CrewOperationPoint.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"

ACityProofCharacter::ACityProofCharacter()
{
    GetCapsuleComponent()->InitCapsuleSize(42.0f, 96.0f);
    GetCapsuleComponent()->SetCollisionProfileName(TEXT("Pawn"));
    GetCharacterMovement()->MaxWalkSpeed = 600.0f;
    bUseControllerRotationYaw = true;
    GetCharacterMovement()->bOrientRotationToMovement = false;

    FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
    FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
    FirstPersonCamera->SetRelativeLocation(FVector(0.0f, 0.0f, 64.0f));
    FirstPersonCamera->bUsePawnControlRotation = true;
}

void ACityProofCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ACityProofCharacter::MoveForward);
    PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ACityProofCharacter::MoveRight);
    PlayerInputComponent->BindAxis(TEXT("Turn"), this, &APawn::AddControllerYawInput);
    PlayerInputComponent->BindAxis(TEXT("LookUp"), this, &APawn::AddControllerPitchInput);
    PlayerInputComponent->BindAction(TEXT("DestroyBridgeAccess"), IE_Pressed, this, &ACityProofCharacter::AttemptBridgeAccessDestruction);
}

void ACityProofCharacter::MoveForward(float Value)
{
    AddMovementInput(GetActorForwardVector(), Value);
}

void ACityProofCharacter::MoveRight(float Value)
{
    AddMovementInput(GetActorRightVector(), Value);
}

void ACityProofCharacter::AttemptBridgeAccessDestruction()
{
    const FVector Start = FirstPersonCamera->GetComponentLocation();
    const FVector End = Start + FirstPersonCamera->GetForwardVector() * 700.0f;
    FHitResult Hit;
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(BridgeAccessDestruction), false, this);
    if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, QueryParams))
    {
        if (ACrewOperationPoint* OperationPoint = Cast<ACrewOperationPoint>(Hit.GetActor()))
        {
            const bool bProposalWritten = OperationPoint->TryResolveByCrew(TEXT("crew_01_to_04"));
            if (GEngine != nullptr)
            {
                GEngine->AddOnScreenDebugMessage(-1, 6.0f, bProposalWritten ? FColor::Green : FColor::Red,
                    bProposalWritten ? TEXT("Physical proposal emitted. Canonical commit required.") : TEXT("No crew-operation proposal emitted."));
            }
            return;
        }
        if (ABridgeAccessPoint* AccessPoint = Cast<ABridgeAccessPoint>(Hit.GetActor()))
        {
            const bool bProposalWritten = AccessPoint->TryDestroyByCrew(TEXT("crew_01_to_04"));
            if (GEngine != nullptr)
            {
                GEngine->AddOnScreenDebugMessage(-1, 6.0f, bProposalWritten ? FColor::Green : FColor::Red,
                    bProposalWritten ? TEXT("Physical proposal emitted. Canonical commit required.") : TEXT("No bridge-access proposal emitted."));
            }
            return;
        }
    }

    for (TActorIterator<ACrewOperationPoint> It(GetWorld()); It; ++It)
    {
        // The proof map is a compressed walkable diagram.  Its B/C operation
        // surfaces remain in the selected materialized domain; the one pawn's
        // interaction reach spans the diagram so UI automation does not become
        // a second, unrelated movement proof.
        if (FVector::DistSquared(GetActorLocation(), It->GetActorLocation()) <= FMath::Square(5000.0f))
        {
            const bool bProposalWritten = It->TryResolveByCrew(TEXT("crew_01_to_04"));
            if (GEngine != nullptr)
            {
                GEngine->AddOnScreenDebugMessage(-1, 6.0f, bProposalWritten ? FColor::Green : FColor::Red,
                    bProposalWritten ? TEXT("Physical proposal emitted. Canonical commit required.") : TEXT("No crew-operation proposal emitted."));
            }
            return;
        }
    }

    // The console sits beside the route, while its owning bridge-access actor
    // remains centered on the route so destroyed geometry materializes in place.
    // A tight proximity fallback keeps the physical interaction local without
    // making a line-trace miss an authority decision.
    for (TActorIterator<ABridgeAccessPoint> It(GetWorld()); It; ++It)
    {
        if (FVector::DistSquared(GetActorLocation(), It->GetActorLocation()) <= FMath::Square(850.0f))
        {
            const bool bProposalWritten = It->TryDestroyByCrew(TEXT("crew_01_to_04"));
            if (GEngine != nullptr)
            {
                GEngine->AddOnScreenDebugMessage(-1, 6.0f, bProposalWritten ? FColor::Green : FColor::Red,
                    bProposalWritten ? TEXT("Physical proposal emitted. Canonical commit required.") : TEXT("No bridge-access proposal emitted."));
            }
            return;
        }
    }

    if (GEngine != nullptr)
    {
        GEngine->AddOnScreenDebugMessage(-1, 3.0f, FColor::Yellow, TEXT("Move within the bridge access point, then press E."));
    }
}
