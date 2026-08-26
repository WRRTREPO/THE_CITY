#include "CrewOperationPoint.h"

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
constexpr TCHAR SimulationVersion[] = TEXT("0.7.0-draft.16");
constexpr TCHAR RuntimeInstanceId[] = TEXT("deployment_opportunity_runtime_01");
constexpr TCHAR FireProposalId[] = TEXT("physical_contain_fire_B_deployment_0001");
constexpr TCHAR DisruptionProposalId[] = TEXT("physical_disrupt_seizure_C_deployment_0001");
constexpr TCHAR FireActorId[] = TEXT("fire_control_valve_B_01");
constexpr TCHAR RelayActorId[] = TEXT("gang_signal_relay_C_01");
}

ACrewOperationPoint::ACrewOperationPoint()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void ACrewOperationPoint::Configure(const FString& InSourceRecordHash, const FString& InExchangeDirectory, const FString& InOperationDomain, bool bInitiallyResolved)
{
    SourceRecordHash = InSourceRecordHash;
    ExchangeDirectory = InExchangeDirectory;
    OperationDomain = InOperationDomain;
    bResolved = bInitiallyResolved;
    if (bResolved)
    {
        BuildResolved();
    }
    else
    {
        BuildInteractable();
    }
}

bool ACrewOperationPoint::IsFireControl() const
{
    return OperationDomain == TEXT("B");
}

UStaticMeshComponent* ACrewOperationPoint::AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bBlocksPawn)
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

UTextRenderComponent* ACrewOperationPoint::AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color)
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

void ACrewOperationPoint::BuildInteractable()
{
    const FString Label = IsFireControl()
        ? TEXT("FIRE CONTROL B — PRESS E TO CONTAIN")
        : TEXT("SEIZURE RELAY C — PRESS E TO DISRUPT");
    InteractableConsole = AddBlock(FVector::ZeroVector, FVector(0.45f, 0.45f, 1.1f), FLinearColor(0.08f, 0.85f, 0.78f), false);
    AddBlock(FVector(0.0f, 0.0f, 15.0f), FVector(0.9f, 0.9f, 0.15f), FLinearColor(0.18f, 0.18f, 0.22f), true);
    InteractableLabel = AddLabel(FVector(0.0f, 0.0f, 250.0f), Label, FColor::Cyan);
}

void ACrewOperationPoint::BuildResolved()
{
    const FString Label = IsFireControl()
        ? TEXT("FIRE CONTAINED — CANONICAL COMMIT REQUIRED")
        : TEXT("SEIZURE RELAY DISABLED — CANONICAL COMMIT REQUIRED");
    AddBlock(FVector(0.0f, 0.0f, 90.0f), FVector(0.65f, 0.65f, 0.35f), FLinearColor(0.10f, 0.32f, 0.25f), true);
    AddLabel(FVector(0.0f, 0.0f, 250.0f), Label, FColor::Green);
}

bool ACrewOperationPoint::TryResolveByCrew(const FString& CrewId)
{
    if (bResolved || SourceRecordHash.IsEmpty() || (OperationDomain != TEXT("B") && OperationDomain != TEXT("C")))
    {
        return false;
    }

    bResolved = true;
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
    BuildResolved();
    const bool bWritten = WritePhysicalProposal(CrewId);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("Physical crew operation detected in %s; proposal %s."), *OperationDomain, bWritten ? TEXT("written") : TEXT("write failed"));
    return bWritten;
}

bool ACrewOperationPoint::WritePhysicalProposal(const FString& CrewId) const
{
    const bool bFire = IsFireControl();
    const TCHAR* ProposalId = bFire ? FireProposalId : DisruptionProposalId;
    const TCHAR* TargetId = bFire ? FireActorId : RelayActorId;
    const TCHAR* TargetKind = bFire ? TEXT("fire_control") : TEXT("gang_signal_relay");
    const TCHAR* OutcomeState = bFire ? TEXT("contained") : TEXT("disabled");
    const TCHAR* Mutation = bFire ? TEXT("B.fire_containment = true") : TEXT("C.crew_disruption = true");
    const TCHAR* Filename = bFire ? TEXT("physical_contain_fire_B_deployment_0001.json") : TEXT("physical_disrupt_seizure_C_deployment_0001.json");
    const FString DigestMaterial = FString::Printf(TEXT("%s|%s|%s|%s|1"), *SourceRecordHash, *CrewId, TargetId, OutcomeState);
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
    Target->SetStringField(TEXT("kind"), TargetKind);
    Target->SetStringField(TEXT("id"), TargetId);
    Target->SetStringField(TEXT("area"), OperationDomain);
    Root->SetObjectField(TEXT("target"), Target);
    TSharedPtr<FJsonObject> Observed = MakeShared<FJsonObject>();
    Observed->SetStringField(TEXT("state"), OutcomeState);
    Observed->SetNumberField(TEXT("event_sequence"), 1);
    Root->SetObjectField(TEXT("observed_outcome"), Observed);
    TSharedPtr<FJsonObject> Evidence = MakeShared<FJsonObject>();
    Evidence->SetStringField(TEXT("physical_actor_id"), TargetId);
    Evidence->SetStringField(TEXT("outcome_state"), OutcomeState);
    Evidence->SetStringField(TEXT("evidence_digest"), Digest);
    Root->SetObjectField(TEXT("evidence"), Evidence);
    TArray<TSharedPtr<FJsonValue>> Mutations;
    Mutations.Add(MakeShared<FJsonValueString>(Mutation));
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
