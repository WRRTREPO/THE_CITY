#include "LiveCommitmentRelayPoint.h"

#include "CityMaterializationProof.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "HAL/FileManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Serialization/JsonSerializer.h"

namespace
{
constexpr TCHAR SimulationVersion[] = TEXT("0.7.0-draft.21");
constexpr TCHAR RuntimeInstanceId[] = TEXT("live_commitment_runtime_01");
constexpr TCHAR RelayActorId[] = TEXT("gang_claim_relay_C_01");
constexpr TCHAR ActiveProposalId[] = TEXT("physical_disable_claim_relay_C_live_0001");
constexpr TCHAR SettledProposalId[] = TEXT("physical_disable_claim_relay_C_live_0002");
}

ALiveCommitmentRelayPoint::ALiveCommitmentRelayPoint()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void ALiveCommitmentRelayPoint::Configure(const FString& InSourceRecordHash, const FString& InExchangeDirectory, const FString& InClaimState, bool bRelayInitiallyActive)
{
    SourceRecordHash = InSourceRecordHash;
    ExchangeDirectory = InExchangeDirectory;
    ClaimState = InClaimState;
    bRelayActive = bRelayInitiallyActive;
    if (bRelayActive)
    {
        BuildInteractable();
    }
    else
    {
        BuildDisabled();
    }
}

UStaticMeshComponent* ALiveCommitmentRelayPoint::AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bBlocksPawn)
{
    UStaticMeshComponent* Block = NewObject<UStaticMeshComponent>(this);
    Block->SetupAttachment(SceneRoot);
    Block->SetStaticMesh(CubeMesh);
    Block->SetRelativeLocation(RelativeLocation);
    Block->SetRelativeScale3D(Scale);
    if (bBlocksPawn)
    {
        Block->SetCollisionProfileName(TEXT("BlockAll"));
        Block->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Block->SetCollisionResponseToAllChannels(ECR_Block);
    }
    else
    {
        Block->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Block->SetCollisionResponseToAllChannels(ECR_Ignore);
        Block->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    }
    if (ShapeMaterial != nullptr)
    {
        UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(ShapeMaterial, this);
        Material->SetVectorParameterValue(TEXT("Color"), Color);
        Block->SetMaterial(0, Material);
    }
    Block->RegisterComponent();
    return Block;
}

UTextRenderComponent* ALiveCommitmentRelayPoint::AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color)
{
    UTextRenderComponent* Label = NewObject<UTextRenderComponent>(this);
    Label->SetupAttachment(SceneRoot);
    Label->SetRelativeLocation(RelativeLocation);
    Label->SetWorldRotation(FRotator(0.0f, 180.0f, 0.0f));
    Label->SetText(FText::FromString(Text));
    Label->SetTextRenderColor(Color);
    Label->SetWorldSize(46.0f);
    Label->SetHorizontalAlignment(EHTA_Center);
    Label->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Label->RegisterComponent();
    return Label;
}

void ALiveCommitmentRelayPoint::BuildInteractable()
{
    const bool bClaimActive = ClaimState == TEXT("active");
    const FString Label = bClaimActive
        ? TEXT("LIVE CLAIM RELAY C — PRESS E TO DISABLE")
        : TEXT("POST-CLAIM RELAY C — PRESS E TO DISABLE");
    InteractableConsole = AddBlock(FVector::ZeroVector, FVector(0.45f, 0.45f, 1.1f), FLinearColor(0.08f, 0.85f, 0.78f), false);
    AddBlock(FVector(0.0f, 0.0f, 15.0f), FVector(0.9f, 0.9f, 0.15f), FLinearColor(0.18f, 0.18f, 0.22f), true);
    InteractableLabel = AddLabel(FVector(0.0f, 0.0f, 250.0f), Label, FColor::Cyan);
}

void ALiveCommitmentRelayPoint::BuildDisabled()
{
    AddBlock(FVector(0.0f, 0.0f, 90.0f), FVector(0.65f, 0.65f, 0.35f), FLinearColor(0.10f, 0.32f, 0.25f), true);
    AddLabel(
        FVector(0.0f, 0.0f, 250.0f),
        bProposalEmitted
            ? TEXT("PHYSICAL RELAY DISABLED — CANONICAL COMMIT REQUIRED")
            : TEXT("RELAY DISABLED — CANONICAL FACT"),
        FColor::Green);
}

bool ALiveCommitmentRelayPoint::TryDisableByCrew(const FString& CrewId)
{
    if (!bRelayActive || SourceRecordHash.IsEmpty() || (ClaimState != TEXT("active") && ClaimState != TEXT("succeeded")))
    {
        return false;
    }

    bRelayActive = false;
    bProposalEmitted = true;
    if (InteractableConsole != nullptr)
    {
        InteractableConsole->DestroyComponent();
        InteractableConsole = nullptr;
    }
    if (InteractableLabel != nullptr)
    {
        InteractableLabel->DestroyComponent();
        InteractableLabel = nullptr;
    }
    BuildDisabled();
    const bool bWritten = WritePhysicalProposal(CrewId);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("Physical live relay disable detected; proposal %s."), bWritten ? TEXT("written") : TEXT("write failed"));
    return bWritten;
}

bool ALiveCommitmentRelayPoint::WritePhysicalProposal(const FString& CrewId) const
{
    const bool bClaimActive = ClaimState == TEXT("active");
    const TCHAR* ProposalId = bClaimActive ? ActiveProposalId : SettledProposalId;
    const int32 EventSequence = bClaimActive ? 1 : 2;
    const TCHAR* Filename = bClaimActive
        ? TEXT("physical_disable_claim_relay_C_live_0001.json")
        : TEXT("physical_disable_claim_relay_C_live_0002.json");
    const FString DigestMaterial = FString::Printf(TEXT("%s|%s|%s|disabled|%d"), *SourceRecordHash, *CrewId, RelayActorId, EventSequence);
    const FString Digest = FString::Printf(TEXT("md5:%s"), *FMD5::HashAnsiString(*DigestMaterial));

    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("proposal_id"), ProposalId);
    Root->SetStringField(TEXT("protocol_version"), TEXT("PhysicalConsequenceProposal.v1"));
    TSharedPtr<FJsonObject> Source = MakeShared<FJsonObject>();
    Source->SetStringField(TEXT("system"), TEXT("crew_physical_simulation"));
    Source->SetStringField(TEXT("runtime_instance_id"), RuntimeInstanceId);
    Source->SetStringField(TEXT("source_record_hash"), SourceRecordHash);
    Source->SetStringField(TEXT("source_simulation_version"), SimulationVersion);
    Root->SetObjectField(TEXT("source"), Source);
    TSharedPtr<FJsonObject> Instigator = MakeShared<FJsonObject>();
    Instigator->SetStringField(TEXT("kind"), TEXT("crew"));
    Instigator->SetStringField(TEXT("id"), CrewId);
    Root->SetObjectField(TEXT("instigator"), Instigator);
    TSharedPtr<FJsonObject> Target = MakeShared<FJsonObject>();
    Target->SetStringField(TEXT("kind"), TEXT("claim_relay"));
    Target->SetStringField(TEXT("id"), RelayActorId);
    Target->SetStringField(TEXT("area"), TEXT("C"));
    Root->SetObjectField(TEXT("target"), Target);
    TSharedPtr<FJsonObject> Observed = MakeShared<FJsonObject>();
    Observed->SetStringField(TEXT("state"), TEXT("disabled"));
    Observed->SetNumberField(TEXT("event_sequence"), EventSequence);
    Root->SetObjectField(TEXT("observed_outcome"), Observed);
    TSharedPtr<FJsonObject> Evidence = MakeShared<FJsonObject>();
    Evidence->SetStringField(TEXT("physical_actor_id"), RelayActorId);
    Evidence->SetStringField(TEXT("outcome_state"), TEXT("disabled"));
    Evidence->SetStringField(TEXT("evidence_digest"), Digest);
    Root->SetObjectField(TEXT("evidence"), Evidence);
    TArray<TSharedPtr<FJsonValue>> Mutations;
    Mutations.Add(MakeShared<FJsonValueString>(TEXT("C.relay.active = false")));
    Root->SetArrayField(TEXT("proposed_mutations"), Mutations);

    FString Serialized;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Serialized);
    if (!FJsonSerializer::Serialize(Root.ToSharedRef(), Writer))
    {
        return false;
    }
    IFileManager::Get().MakeDirectory(*ExchangeDirectory, true);
    return FFileHelper::SaveStringToFile(Serialized, *FPaths::Combine(ExchangeDirectory, Filename));
}
