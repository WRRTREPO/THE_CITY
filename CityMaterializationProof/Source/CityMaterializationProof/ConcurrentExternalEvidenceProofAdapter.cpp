#include "ConcurrentExternalEvidenceProofAdapter.h"

#include "CityMaterializationProof.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "ConcurrentEvidenceSurface.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#include <openssl/sha.h>

namespace
{
constexpr TCHAR RecordSchema[] = TEXT("CanonicalResolutionEnvelope.v1");
constexpr TCHAR PayloadSchema[] = TEXT("ConcurrentExternalEvidenceArbitrationPayload.v1");
constexpr TCHAR ScenarioId[] = TEXT("concurrent-external-evidence-arbitration-v1");
constexpr TCHAR SimulationVersion[] = TEXT("0.7.0-draft.57");
constexpr TCHAR Opportunity[] = TEXT("t0/30");

const FString FrozenR0Canonical =
    TEXT("{\"causal_provenance\":{\"adjudicated_external_input_ids\":[],\"adjudicated_physical_event_ids\":[],\"authoritative_causal_ledger\":[],\"canonical_ancestry\":null,\"fixture_genesis\":{\"source\":\"frozen_initial_fixture\"}},\"current_causal_state\":{\"external_consequence_contracts\":{\"domain_A\":{\"observed_outcome\":\"allocation_requested\",\"permitted_input_id\":\"physical_allocate_shared_slot_A_0001\",\"permitted_owner\":\"domain_A\",\"permitted_physical_event_id\":\"domain_A_allocation_event_0001\",\"physical_actor_id\":\"arbitration_surface_A_01\",\"target\":{\"id\":\"shared_slot_01\",\"kind\":\"proof_shared_slot\"}},\"domain_B\":{\"observed_outcome\":\"allocation_requested\",\"permitted_input_id\":\"physical_allocate_shared_slot_B_0001\",\"permitted_owner\":\"domain_B\",\"permitted_physical_event_id\":\"domain_B_allocation_event_0001\",\"physical_actor_id\":\"arbitration_surface_B_01\",\"target\":{\"id\":\"shared_slot_01\",\"kind\":\"proof_shared_slot\"}}},\"shared_slot\":{\"allocation_owner\":null}},\"future_causal_state\":{\"canonical_clock\":\"t0/00\",\"unresolved_work\":[]},\"identity\":{\"payload_schema\":\"ConcurrentExternalEvidenceArbitrationPayload.v1\",\"record_schema\":\"CanonicalResolutionEnvelope.v1\",\"scenario_id\":\"concurrent-external-evidence-arbitration-v1\",\"scenario_version\":\"0.1.0\",\"seed\":\"concurrent-external-evidence-arbitration-v1/0001\",\"simulation_version\":\"0.7.0-draft.57\"}}");

FString Sha256Hex(const uint8* Data, int32 Length)
{
    uint8 Digest[SHA256_DIGEST_LENGTH];
    SHA256(Data, Length, Digest);
    FString Result;
    for (uint8 Byte : Digest)
    {
        Result += FString::Printf(TEXT("%02x"), Byte);
    }
    return Result;
}

FString Sha256Hex(const FString& Value)
{
    FTCHARToUTF8 Utf8(*Value);
    return Sha256Hex(reinterpret_cast<const uint8*>(Utf8.Get()), Utf8.Length());
}

bool IsAsciiNonEmpty(const FString& Value)
{
    if (Value.IsEmpty())
    {
        return false;
    }
    for (TCHAR Character : Value)
    {
        if (Character < 0x21 || Character > 0x7e)
        {
            return false;
        }
    }
    return true;
}

bool LoadExactStoredJson(const FString& Path, TArray<uint8>& OutBytes, FString& OutCanonical, FString& OutFailure)
{
    if (!FFileHelper::LoadFileToArray(OutBytes, *Path) || OutBytes.Num() < 2 || OutBytes.Last() != '\n')
    {
        OutFailure = TEXT("concurrent proof input cannot be read or lacks one terminal LF");
        return false;
    }
    int32 NewlineCount = 0;
    for (uint8 Byte : OutBytes)
    {
        NewlineCount += Byte == '\n' ? 1 : 0;
        if (Byte == '\r')
        {
            OutFailure = TEXT("concurrent proof input contains CR bytes");
            return false;
        }
    }
    if (NewlineCount != 1)
    {
        OutFailure = TEXT("concurrent proof input violates exact LF serialization");
        return false;
    }
    FUTF8ToTCHAR Converter(reinterpret_cast<const ANSICHAR*>(OutBytes.GetData()), OutBytes.Num() - 1);
    OutCanonical = FString(Converter.Length(), Converter.Get());
    return true;
}
}

AConcurrentExternalEvidenceProofAdapter::AConcurrentExternalEvidenceProofAdapter()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void AConcurrentExternalEvidenceProofAdapter::BeginPlay()
{
    Super::BeginPlay();
    FConcurrentEvidenceMaterializationRecord Record;
    FString Failure;
    if (!LoadAndVerify(Record, Failure))
    {
        UE_LOG(LogCityMaterializationProof, Error, TEXT("Concurrent evidence proof refused materialization: %s"), *Failure);
        AddLabel(FVector(0.0f, 0.0f, 400.0f), FString::Printf(TEXT("CONCURRENT PROOF REFUSED\n%s"), *Failure), FColor::Red);
        return;
    }
    Materialize(Record);
    EmitAcceptanceReceipt(Record);
}

bool AConcurrentExternalEvidenceProofAdapter::LoadAndVerify(FConcurrentEvidenceMaterializationRecord& OutRecord, FString& OutFailure) const
{
    FString PayloadPath;
    FString ReceiptPath;
    FString OutputDirectory;
    FString InteractionOpportunity;
    FString ProcessInstanceId;
    FString SourceDomain;
    FParse::Value(FCommandLine::Get(), TEXT("ConcurrentEvidencePayload="), PayloadPath);
    FParse::Value(FCommandLine::Get(), TEXT("ConcurrentEvidenceLaunchReceipt="), ReceiptPath);
    FParse::Value(FCommandLine::Get(), TEXT("ConcurrentEvidenceOutput="), OutputDirectory);
    FParse::Value(FCommandLine::Get(), TEXT("ConcurrentEvidenceInteractionOpportunity="), InteractionOpportunity);
    FParse::Value(FCommandLine::Get(), TEXT("ConcurrentEvidenceProcessInstanceId="), ProcessInstanceId);
    FParse::Value(FCommandLine::Get(), TEXT("ConcurrentEvidenceDomain="), SourceDomain);
    const FString CommandLine = FCommandLine::Get();
    if (PayloadPath.IsEmpty() || ReceiptPath.IsEmpty() || OutputDirectory.IsEmpty() || !IsAsciiNonEmpty(ProcessInstanceId) ||
        InteractionOpportunity != Opportunity || (SourceDomain != TEXT("domain_A") && SourceDomain != TEXT("domain_B")) ||
        CommandLine.Contains(TEXT("IntegratedProofPayload=")) || CommandLine.Contains(TEXT("CityProofRecord=")) ||
        CommandLine.Contains(TEXT("CityProofExchange=")) || CommandLine.Contains(TEXT("CityProof=")) ||
        CommandLine.Contains(TEXT("ConcurrentEvidencePriority=")) || CommandLine.Contains(TEXT("ConcurrentEvidenceExternalPhase=")) ||
        CommandLine.Contains(TEXT("ConcurrentEvidenceMemberOrder=")) || CommandLine.Contains(TEXT("ConcurrentEvidenceWinner=")))
    {
        OutFailure = TEXT("concurrent proof input contract is incomplete or contains an authority-bearing selector");
        return false;
    }

    TArray<uint8> PayloadBytes;
    TArray<uint8> ReceiptBytes;
    FString PayloadCanonical;
    FString ReceiptCanonical;
    if (!LoadExactStoredJson(PayloadPath, PayloadBytes, PayloadCanonical, OutFailure) ||
        !LoadExactStoredJson(ReceiptPath, ReceiptBytes, ReceiptCanonical, OutFailure))
    {
        return false;
    }
    if (PayloadCanonical != FrozenR0Canonical)
    {
        OutFailure = TEXT("payload is not the exact frozen concurrent R0");
        return false;
    }

    const FString CanonicalHash = Sha256Hex(FrozenR0Canonical);
    const FString RawPayloadHash = Sha256Hex(PayloadBytes.GetData(), PayloadBytes.Num());
    const FString ExpectedReceipt = FString::Printf(
        TEXT("{\"artifact_role\":\"canonical_materialization_input\",\"canonical_hash\":\"%s\",\"expected_payload_schema\":\"%s\",\"expected_record_schema\":\"%s\",\"expected_scenario_id\":\"%s\",\"expected_simulation_version\":\"%s\",\"raw_byte_sha256\":\"%s\",\"receipt_schema\":\"ConcurrentUnrealLaunchReceipt.v1\"}"),
        *CanonicalHash, PayloadSchema, RecordSchema, ScenarioId, SimulationVersion, *RawPayloadHash);
    if (ReceiptCanonical != ExpectedReceipt)
    {
        OutFailure = TEXT("detached launch receipt does not bind the exact frozen R0 bytes and identity");
        return false;
    }

    OutRecord.CanonicalHash = CanonicalHash;
    OutRecord.RawPayloadHash = RawPayloadHash;
    OutRecord.OutputDirectory = OutputDirectory;
    OutRecord.InteractionOpportunity = InteractionOpportunity;
    OutRecord.ProcessInstanceId = ProcessInstanceId;
    OutRecord.SourceDomain = SourceDomain;
    OutRecord.PhysicalActorId = SourceDomain == TEXT("domain_A") ? TEXT("arbitration_surface_A_01") : TEXT("arbitration_surface_B_01");
    return true;
}

UStaticMeshComponent* AConcurrentExternalEvidenceProofAdapter::AddBlock(const FVector& Location, const FVector& Scale, const FLinearColor& Color, bool bBlocksMovement)
{
    UStaticMeshComponent* Block = NewObject<UStaticMeshComponent>(this);
    Block->SetupAttachment(SceneRoot);
    Block->SetStaticMesh(CubeMesh);
    Block->SetWorldLocation(Location);
    Block->SetWorldScale3D(Scale);
    if (bBlocksMovement)
    {
        Block->SetCollisionProfileName(TEXT("BlockAll"));
        Block->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Block->SetCollisionResponseToAllChannels(ECR_Block);
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

UTextRenderComponent* AConcurrentExternalEvidenceProofAdapter::AddLabel(const FVector& Location, const FString& Text, const FColor& Color)
{
    UTextRenderComponent* Label = NewObject<UTextRenderComponent>(this);
    Label->SetupAttachment(SceneRoot);
    Label->SetWorldLocation(Location);
    Label->SetWorldRotation(FRotator(0.0f, 180.0f, 0.0f));
    Label->SetText(FText::FromString(Text));
    Label->SetTextRenderColor(Color);
    Label->SetWorldSize(50.0f);
    Label->SetHorizontalAlignment(EHTA_Center);
    Label->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Label->RegisterComponent();
    return Label;
}

void AConcurrentExternalEvidenceProofAdapter::Materialize(const FConcurrentEvidenceMaterializationRecord& Record)
{
    UPointLightComponent* KeyLight = NewObject<UPointLightComponent>(this, TEXT("ConcurrentProofKeyLight"));
    KeyLight->SetupAttachment(SceneRoot);
    KeyLight->SetWorldLocation(FVector(-500.0f, -350.0f, 1500.0f));
    KeyLight->SetIntensity(180000.0f);
    KeyLight->SetAttenuationRadius(7000.0f);
    KeyLight->SetLightColor(FLinearColor(0.82f, 0.90f, 1.0f));
    KeyLight->RegisterComponent();

    AddBlock(FVector(0.0f, 0.0f, -20.0f), FVector(40.0f, 20.0f, 0.4f), FLinearColor(0.12f, 0.14f, 0.18f), true);
    AddLabel(FVector(-820.0f, -420.0f, 360.0f), FString::Printf(
        TEXT("CONCURRENT EXTERNAL EVIDENCE\ncanonical: %s\ndomain: %s | shared slot: AVAILABLE\nproposal capability: ENABLED"),
        *Record.CanonicalHash.Left(12), *Record.SourceDomain.ToUpper()), FColor::White);
    if (AConcurrentEvidenceSurface* Surface = GetWorld()->SpawnActor<AConcurrentEvidenceSurface>(
        AConcurrentEvidenceSurface::StaticClass(), FVector(0.0f, 220.0f, 0.0f), FRotator::ZeroRotator))
    {
        Surface->Configure(Record.CanonicalHash, Record.RawPayloadHash, Record.OutputDirectory,
            Record.InteractionOpportunity, Record.ProcessInstanceId, Record.SourceDomain);
    }
}

void AConcurrentExternalEvidenceProofAdapter::EmitAcceptanceReceipt(const FConcurrentEvidenceMaterializationRecord& Record) const
{
    const FString Json = FString::Printf(
        TEXT("{\"accepted_canonical_hash\":\"%s\",\"accepted_raw_payload_sha256\":\"%s\",\"materialization_domain\":\"%s\",\"materialized_physical_actor_id\":\"%s\",\"materialized_shared_slot_owner\":null,\"process_instance_id\":\"%s\",\"proposal_capability_enabled\":true,\"receipt_schema\":\"ConcurrentMaterializationAcceptanceReceipt.v1\"}"),
        *Record.CanonicalHash, *Record.RawPayloadHash, *Record.SourceDomain, *Record.PhysicalActorId, *Record.ProcessInstanceId);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("CONCURRENT_MATERIALIZATION_RECEIPT:%s"), *Json);
}
