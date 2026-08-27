#include "ConcurrentEvidenceSurface.h"

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

AConcurrentEvidenceSurface::AConcurrentEvidenceSurface()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void AConcurrentEvidenceSurface::Configure(
    const FString& InCanonicalHash,
    const FString& InRawPayloadHash,
    const FString& InOutputDirectory,
    const FString& InInteractionOpportunity,
    const FString& InProcessInstanceId,
    const FString& InSourceDomain)
{
    CanonicalHash = InCanonicalHash;
    RawPayloadHash = InRawPayloadHash;
    OutputDirectory = InOutputDirectory;
    InteractionOpportunity = InInteractionOpportunity;
    ProcessInstanceId = InProcessInstanceId;
    SourceDomain = InSourceDomain;

    if (SourceDomain == TEXT("domain_A"))
    {
        PhysicalActorId = TEXT("arbitration_surface_A_01");
        InputId = TEXT("physical_allocate_shared_slot_A_0001");
        PhysicalEventId = TEXT("domain_A_allocation_event_0001");
        AllocationOwner = TEXT("domain_A");
    }
    else
    {
        PhysicalActorId = TEXT("arbitration_surface_B_01");
        InputId = TEXT("physical_allocate_shared_slot_B_0001");
        PhysicalEventId = TEXT("domain_B_allocation_event_0001");
        AllocationOwner = TEXT("domain_B");
    }

    const FLinearColor DomainColor = SourceDomain == TEXT("domain_A")
        ? FLinearColor(0.08f, 0.78f, 0.92f)
        : FLinearColor(0.92f, 0.40f, 0.12f);
    InteractionSurface = AddBlock(FVector::ZeroVector, FVector(0.65f, 0.65f, 1.15f), DomainColor, true);
    AddBlock(FVector(0.0f, 0.0f, 15.0f), FVector(1.05f, 1.05f, 0.15f), FLinearColor(0.18f, 0.18f, 0.22f), false);
    InteractionLabel = AddLabel(
        FVector(0.0f, 0.0f, 260.0f),
        FString::Printf(TEXT("CONCURRENT EVIDENCE %s\nSHARED SLOT AVAILABLE — PRESS E\nCANONICAL BATCH REQUIRED"), *SourceDomain.ToUpper()),
        SourceDomain == TEXT("domain_A") ? FColor::Cyan : FColor::Orange);
}

UStaticMeshComponent* AConcurrentEvidenceSurface::AddBlock(const FVector& RelativeLocation, const FVector& Scale, const FLinearColor& Color, bool bInteractable)
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

UTextRenderComponent* AConcurrentEvidenceSurface::AddLabel(const FVector& RelativeLocation, const FString& Text, const FColor& Color)
{
    UTextRenderComponent* Label = NewObject<UTextRenderComponent>(this);
    Label->SetupAttachment(SceneRoot);
    Label->SetRelativeLocation(RelativeLocation);
    Label->SetWorldRotation(FRotator(0.0f, 180.0f, 0.0f));
    Label->SetText(FText::FromString(Text));
    Label->SetTextRenderColor(Color);
    Label->SetWorldSize(43.0f);
    Label->SetHorizontalAlignment(EHTA_Center);
    Label->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Label->RegisterComponent();
    return Label;
}

bool AConcurrentEvidenceSurface::TryAllocateByCrew(const FString& CrewId)
{
    if (bEvidenceEmitted || CrewId != TEXT("crew_01_to_04") || CanonicalHash.IsEmpty() || RawPayloadHash.IsEmpty() ||
        OutputDirectory.IsEmpty() || ProcessInstanceId.IsEmpty() || InteractionOpportunity != Opportunity ||
        (SourceDomain != TEXT("domain_A") && SourceDomain != TEXT("domain_B")))
    {
        return false;
    }

    if (!WriteExactEvidence())
    {
        UE_LOG(LogCityMaterializationProof, Error, TEXT("Concurrent physical evidence write failed for %s."), *SourceDomain);
        return false;
    }

    bEvidenceEmitted = true;
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
    AddBlock(FVector(0.0f, 0.0f, 90.0f), FVector(0.78f, 0.78f, 0.35f), FLinearColor(0.16f, 0.48f, 0.24f), false);
    AddLabel(FVector(0.0f, 0.0f, 260.0f), TEXT("PHYSICAL ALLOCATION EVIDENCED\nCANONICAL BATCH REQUIRED"), FColor::Green);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("Concurrent physical evidence emitted for %s."), *SourceDomain);
    return true;
}

bool AConcurrentEvidenceSurface::WriteExactEvidence()
{
    // Frozen canonical_json(Q digest projection): lexical keys, compact
    // separators, ASCII-only fixture values, evidence_digest absent.
    const FString Projection = FString::Printf(
        TEXT("{\"evidence\":{\"outcome_state\":\"allocation_requested\",\"physical_actor_id\":\"%s\"},\"input_id\":\"%s\",\"observed_outcome\":{\"state\":\"allocation_requested\"},\"occurrence_time\":\"t0/30\",\"physical_event_id\":\"%s\",\"proposed_effect\":{\"op\":\"replace\",\"path\":\"/current_causal_state/shared_slot/allocation_owner\",\"value\":\"%s\"},\"protocol_version\":\"ConcurrentExternalEvidence.v1\",\"source\":{\"domain\":\"%s\",\"source_payload_raw_sha256\":\"%s\",\"source_record_hash\":\"%s\",\"system\":\"crew_physical_simulation\"},\"target\":{\"id\":\"shared_slot_01\",\"kind\":\"proof_shared_slot\"}}"),
        *PhysicalActorId, *InputId, *PhysicalEventId, *AllocationOwner, *SourceDomain, *RawPayloadHash, *CanonicalHash);
    const FString EvidenceDigest = Sha256Hex(Projection);
    const FString QCanonical = FString::Printf(
        TEXT("{\"evidence\":{\"evidence_digest\":\"%s\",\"outcome_state\":\"allocation_requested\",\"physical_actor_id\":\"%s\"},\"input_id\":\"%s\",\"observed_outcome\":{\"state\":\"allocation_requested\"},\"occurrence_time\":\"t0/30\",\"physical_event_id\":\"%s\",\"proposed_effect\":{\"op\":\"replace\",\"path\":\"/current_causal_state/shared_slot/allocation_owner\",\"value\":\"%s\"},\"protocol_version\":\"ConcurrentExternalEvidence.v1\",\"source\":{\"domain\":\"%s\",\"source_payload_raw_sha256\":\"%s\",\"source_record_hash\":\"%s\",\"system\":\"crew_physical_simulation\"},\"target\":{\"id\":\"shared_slot_01\",\"kind\":\"proof_shared_slot\"}}"),
        *EvidenceDigest, *PhysicalActorId, *InputId, *PhysicalEventId, *AllocationOwner, *SourceDomain, *RawPayloadHash, *CanonicalHash);
    const FString QStored = QCanonical + TEXT("\n");
    const FString QCanonicalHash = Sha256Hex(QCanonical);
    const FString QRawHash = Sha256Hex(QStored);
    const FString Receipt = FString::Printf(
        TEXT("{\"accepted_canonical_hash\":\"%s\",\"accepted_raw_payload_sha256\":\"%s\",\"emitted_input_id\":\"%s\",\"emitted_physical_event_id\":\"%s\",\"emitted_q_canonical_hash\":\"%s\",\"emitted_q_raw_sha256\":\"%s\",\"materialization_domain\":\"%s\",\"materialized_physical_actor_id\":\"%s\",\"process_instance_id\":\"%s\",\"receipt_schema\":\"ConcurrentEvidenceEmissionReceipt.v1\"}\n"),
        *CanonicalHash, *RawPayloadHash, *InputId, *PhysicalEventId, *QCanonicalHash, *QRawHash, *SourceDomain, *PhysicalActorId, *ProcessInstanceId);

    IFileManager::Get().MakeDirectory(*OutputDirectory, true);
    const FString QPath = FPaths::Combine(OutputDirectory, InputId + TEXT(".json"));
    const FString ReceiptPath = FPaths::Combine(OutputDirectory, InputId + TEXT(".emission_receipt.json"));
    if (IFileManager::Get().FileExists(*QPath) || IFileManager::Get().FileExists(*ReceiptPath))
    {
        return false;
    }
    if (!FFileHelper::SaveStringToFile(QStored, *QPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        return false;
    }
    if (!FFileHelper::SaveStringToFile(Receipt, *ReceiptPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        IFileManager::Get().Delete(*QPath, false, true);
        return false;
    }
    return true;
}
