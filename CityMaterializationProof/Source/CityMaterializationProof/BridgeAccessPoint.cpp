#include "BridgeAccessPoint.h"

#include "CityMaterializationProof.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Serialization/JsonSerializer.h"

namespace
{
constexpr TCHAR RoundTripProposalId[] = TEXT("physical_destroy_E_AB_0001");
constexpr TCHAR ContentionProposalId[] = TEXT("physical_destroy_E_AB_contention_0001");
constexpr TCHAR TargetId[] = TEXT("bridge_access_point_E_AB_01");
constexpr TCHAR RoundTripSimulationVersion[] = TEXT("0.7.0-draft.9");
constexpr TCHAR ContentionSimulationVersion[] = TEXT("0.7.0-draft.13");
}

ABridgeAccessPoint::ABridgeAccessPoint()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void ABridgeAccessPoint::Configure(const FString& InSourceRecordHash, const FString& InExchangeDirectory, bool bInitiallyDestroyed, bool bInContentionProof)
{
    SourceRecordHash = InSourceRecordHash;
    ExchangeDirectory = InExchangeDirectory;
    bContentionProof = bInContentionProof;
    bDestroyed = bInitiallyDestroyed;
    if (bDestroyed)
    {
        BuildDestroyed();
    }
    else
    {
        BuildIntact();
    }
}

UStaticMeshComponent* ABridgeAccessPoint::AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bBlocksPawn)
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

UTextRenderComponent* ABridgeAccessPoint::AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color)
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

void ABridgeAccessPoint::BuildIntact()
{
    InteractableConsole = AddBlock(FVector(-180.0f, 250.0f, 105.0f), FVector(0.4f, 0.4f, 1.0f), FLinearColor(0.15f, 0.65f, 0.95f), false);
    AddBlock(FVector(-180.0f, 250.0f, 15.0f), FVector(0.9f, 0.9f, 0.15f), FLinearColor(0.18f, 0.18f, 0.22f), true);
    InteractableLabel = AddLabel(FVector(-180.0f, 250.0f, 260.0f), TEXT("BRIDGE ACCESS — PRESS E TO DESTROY"), FColor::Cyan);
}

void ABridgeAccessPoint::BuildDestroyed()
{
    AddBlock(FVector(0.0f, 0.0f, 125.0f), FVector(0.65f, 2.4f, 1.25f), FLinearColor(0.34f, 0.08f, 0.04f), true);
    AddBlock(FVector(-110.0f, -130.0f, 45.0f), FVector(0.8f, 0.9f, 0.35f), FLinearColor(0.16f, 0.16f, 0.16f), true);
    AddBlock(FVector(140.0f, 170.0f, 35.0f), FVector(0.55f, 0.65f, 0.25f), FLinearColor(0.20f, 0.20f, 0.20f), true);
    AddLabel(FVector(0.0f, 0.0f, 340.0f), TEXT("ACCESS DESTROYED - ROUTE CLOSED"), FColor::Red);
}

bool ABridgeAccessPoint::TryDestroyByCrew(const FString& CrewId)
{
    if (bDestroyed || SourceRecordHash.IsEmpty())
    {
        return false;
    }

    bDestroyed = true;
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
    BuildDestroyed();

    const bool bWritten = WritePhysicalProposal(CrewId);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("Physical bridge-access destruction detected; proposal %s."), bWritten ? TEXT("written") : TEXT("write failed"));
    return bWritten;
}

bool ABridgeAccessPoint::WritePhysicalProposal(const FString& CrewId) const
{
    const TCHAR* ProposalId = bContentionProof ? ContentionProposalId : RoundTripProposalId;
    const TCHAR* SimulationVersion = bContentionProof ? ContentionSimulationVersion : RoundTripSimulationVersion;
    const TCHAR* RuntimeInstanceId = bContentionProof ? TEXT("contention_proof_runtime_01") : TEXT("proof_runtime_01");
    const TCHAR* ProposalFilename = bContentionProof ? TEXT("physical_destroy_E_AB_contention_0001.json") : TEXT("physical_destroy_E_AB_0001.json");
    const FString DigestMaterial = FString::Printf(TEXT("%s|%s|%s|destroyed|1"), *SourceRecordHash, *CrewId, TargetId);
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
    Target->SetStringField(TEXT("kind"), TEXT("bridge_access_point"));
    Target->SetStringField(TEXT("id"), TargetId);
    Target->SetStringField(TEXT("route"), TEXT("E_AB"));
    Root->SetObjectField(TEXT("target"), Target);

    TSharedPtr<FJsonObject> Observed = MakeShared<FJsonObject>();
    Observed->SetStringField(TEXT("state"), TEXT("destroyed"));
    Observed->SetNumberField(TEXT("event_sequence"), 1);
    Root->SetObjectField(TEXT("observed_outcome"), Observed);

    TSharedPtr<FJsonObject> Evidence = MakeShared<FJsonObject>();
    Evidence->SetStringField(TEXT("physical_actor_id"), TargetId);
    Evidence->SetStringField(TEXT("destruction_state"), TEXT("destroyed"));
    Evidence->SetStringField(TEXT("evidence_digest"), Digest);
    Root->SetObjectField(TEXT("evidence"), Evidence);

    TArray<TSharedPtr<FJsonValue>> Mutations;
    Mutations.Add(MakeShared<FJsonValueString>(bContentionProof ? TEXT("E_AB.open = false") : TEXT("E_AB.bridge_open = false")));
    Mutations.Add(MakeShared<FJsonValueString>(TEXT("E_AB.capacity = 0")));
    Mutations.Add(MakeShared<FJsonValueString>(TEXT("E_AB.bridge_access_point.state = destroyed")));
    Root->SetArrayField(TEXT("proposed_mutations"), Mutations);

    FString Serialized;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Serialized);
    if (!FJsonSerializer::Serialize(Root.ToSharedRef(), Writer))
    {
        return false;
    }

    IFileManager::Get().MakeDirectory(*ExchangeDirectory, true);
    const FString ProposalPath = FPaths::Combine(ExchangeDirectory, ProposalFilename);
    return FFileHelper::SaveStringToFile(Serialized, *ProposalPath);
}
