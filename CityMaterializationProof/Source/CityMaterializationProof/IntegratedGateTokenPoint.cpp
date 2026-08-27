#include "IntegratedGateTokenPoint.h"

#include "CityMaterializationProof.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/FileManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

#include <openssl/sha.h>

namespace
{
constexpr TCHAR GateActorId[] = TEXT("integrated_gate_token_01");
constexpr TCHAR InputId[] = TEXT("physical_disable_integrated_gate_token_0001");
constexpr TCHAR Opportunity[] = TEXT("t0/30");

FString Sha256Hex(const FString& Value)
{
    FTCHARToUTF8 Utf8(*Value);
    uint8 Digest[SHA256_DIGEST_LENGTH];
    SHA256(reinterpret_cast<const unsigned char*>(Utf8.Get()), Utf8.Length(), Digest);
    FString Result;
    for (uint8 Byte : Digest)
    {
        Result += FString::Printf(TEXT("%02x"), Byte);
    }
    return Result;
}
}

AIntegratedGateTokenPoint::AIntegratedGateTokenPoint()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void AIntegratedGateTokenPoint::Configure(
    const FString& InCanonicalHash,
    const FString& InRawPayloadHash,
    const FString& InOutputDirectory,
    const FString& InInteractionOpportunity,
    bool bInitiallyEnabled,
    bool bInProposalCapabilityEnabled)
{
    CanonicalHash = InCanonicalHash;
    RawPayloadHash = InRawPayloadHash;
    OutputDirectory = InOutputDirectory;
    InteractionOpportunity = InInteractionOpportunity;
    bEnabled = bInitiallyEnabled;
    bProposalCapabilityEnabled = bInProposalCapabilityEnabled;
    if (bEnabled)
    {
        BuildEnabled();
    }
    else
    {
        BuildDisabled();
    }
}

UStaticMeshComponent* AIntegratedGateTokenPoint::AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bInteractable)
{
    UStaticMeshComponent* Block = NewObject<UStaticMeshComponent>(this);
    Block->SetupAttachment(SceneRoot);
    Block->SetStaticMesh(CubeMesh);
    Block->SetRelativeLocation(RelativeLocation);
    Block->SetRelativeScale3D(Scale);
    if (bInteractable)
    {
        Block->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Block->SetCollisionResponseToAllChannels(ECR_Ignore);
        Block->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    }
    else
    {
        Block->SetCollisionEnabled(ECollisionEnabled::NoCollision);
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

UTextRenderComponent* AIntegratedGateTokenPoint::AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color)
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

void AIntegratedGateTokenPoint::BuildEnabled()
{
    InteractionSurface = AddBlock(FVector::ZeroVector, FVector(0.55f, 0.55f, 1.15f), FLinearColor(0.08f, 0.85f, 0.78f), true);
    AddBlock(FVector(0.0f, 0.0f, 15.0f), FVector(0.95f, 0.95f, 0.15f), FLinearColor(0.18f, 0.18f, 0.22f), false);
    InteractionLabel = AddLabel(
        FVector(0.0f, 0.0f, 250.0f),
        bProposalCapabilityEnabled
            ? TEXT("INTEGRATED GATE ENABLED — PRESS E TO DISABLE\nCANONICAL COMMIT REQUIRED")
            : TEXT("INTEGRATED GATE ENABLED — RETURN MATERIALIZATION"),
        FColor::Cyan);
}

void AIntegratedGateTokenPoint::BuildDisabled()
{
    AddBlock(FVector(0.0f, 0.0f, 90.0f), FVector(0.7f, 0.7f, 0.35f), FLinearColor(0.10f, 0.32f, 0.25f), false);
    AddLabel(
        FVector(0.0f, 0.0f, 250.0f),
        bProposalEmitted
            ? TEXT("PHYSICAL GATE DISABLED — CANONICAL COMMIT REQUIRED")
            : TEXT("INTEGRATED GATE DISABLED — CANONICAL FACT"),
        FColor::Green);
}

bool AIntegratedGateTokenPoint::TryDisableByCrew(const FString& CrewId)
{
    if (!bEnabled || !bProposalCapabilityEnabled || bProposalEmitted || CanonicalHash.IsEmpty() || RawPayloadHash.IsEmpty() ||
        OutputDirectory.IsEmpty() || InteractionOpportunity != Opportunity || CrewId != TEXT("crew_01_to_04"))
    {
        return false;
    }

    bEnabled = false;
    bProposalEmitted = true;
    if (InteractionSurface != nullptr)
    {
        InteractionSurface->DestroyComponent();
        InteractionSurface = nullptr;
    }
    if (InteractionLabel != nullptr)
    {
        InteractionLabel->DestroyComponent();
        InteractionLabel = nullptr;
    }
    BuildDisabled();
    const bool bWritten = WriteExactQ(CrewId);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("Integrated physical gate disable; Q %s."), bWritten ? TEXT("written") : TEXT("write failed"));
    return bWritten;
}

bool AIntegratedGateTokenPoint::WriteExactQ(const FString& CrewId) const
{
    // This is canonical_json(Q_digest_projection): lexical keys, compact
    // separators, ASCII-only fixed fixture values. UE never writes a record.
    const FString Projection = FString::Printf(
        TEXT("{\"evidence\":{\"outcome_state\":\"disabled\",\"physical_actor_id\":\"%s\"},\"input_id\":\"%s\",\"instigator\":{\"id\":\"%s\",\"kind\":\"crew\"},\"observed_outcome\":{\"state\":\"disabled\"},\"occurrence_time\":\"%s\",\"proposed_mutations\":[\"current_causal_state.gate_token.state = disabled\"],\"protocol_version\":\"IntegratedExternalEvidence.v1\",\"source\":{\"source_payload_raw_sha256\":\"%s\",\"source_record_hash\":\"%s\",\"system\":\"crew_physical_simulation\"},\"target\":{\"id\":\"%s\",\"kind\":\"integrated_gate_token\"}}"),
        GateActorId, InputId, *CrewId, Opportunity, *RawPayloadHash, *CanonicalHash, GateActorId);
    const FString Digest = Sha256Hex(Projection);
    const FString Q = FString::Printf(
        TEXT("{\"evidence\":{\"evidence_digest\":\"%s\",\"outcome_state\":\"disabled\",\"physical_actor_id\":\"%s\"},\"input_id\":\"%s\",\"instigator\":{\"id\":\"%s\",\"kind\":\"crew\"},\"observed_outcome\":{\"state\":\"disabled\"},\"occurrence_time\":\"%s\",\"proposed_mutations\":[\"current_causal_state.gate_token.state = disabled\"],\"protocol_version\":\"IntegratedExternalEvidence.v1\",\"source\":{\"source_payload_raw_sha256\":\"%s\",\"source_record_hash\":\"%s\",\"system\":\"crew_physical_simulation\"},\"target\":{\"id\":\"%s\",\"kind\":\"integrated_gate_token\"}}\n"),
        *Digest, GateActorId, InputId, *CrewId, Opportunity, *RawPayloadHash, *CanonicalHash, GateActorId);
    IFileManager::Get().MakeDirectory(*OutputDirectory, true);
    return FFileHelper::SaveStringToFile(Q, *FPaths::Combine(OutputDirectory, TEXT("physical_disable_integrated_gate_token_0001.json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
}
