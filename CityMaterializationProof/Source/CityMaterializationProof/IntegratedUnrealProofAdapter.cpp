#include "IntegratedUnrealProofAdapter.h"

#include "CityMaterializationProof.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Containers/StringConv.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "IntegratedGateTokenPoint.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#include <openssl/sha.h>

namespace
{
constexpr TCHAR RecordSchema[] = TEXT("CanonicalResolutionEnvelope.v1");
constexpr TCHAR PayloadSchema[] = TEXT("IntegratedUnrealPromotionUnloadRepromotionPayload.v1");
constexpr TCHAR ScenarioId[] = TEXT("integrated-unreal-promotion-unload-repromotion-v1");
constexpr TCHAR SimulationVersion[] = TEXT("0.7.0-draft.51");
constexpr TCHAR LaunchReceiptSchema[] = TEXT("IntegratedUnrealLaunchReceipt.v1");
constexpr TCHAR AcceptanceReceiptSchema[] = TEXT("IntegratedMaterializationAcceptanceReceipt.v1");
constexpr TCHAR ActorId[] = TEXT("integrated_gate_token_01");
constexpr TCHAR SourceOpportunity[] = TEXT("t0/30");

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

bool HasExactKeys(const TSharedPtr<FJsonObject>& Object, const TArray<FString>& Keys)
{
    if (!Object.IsValid() || Object->Values.Num() != Keys.Num())
    {
        return false;
    }
    for (const FString& Key : Keys)
    {
        if (!Object->HasField(Key))
        {
            return false;
        }
    }
    return true;
}

bool ReadStrictCanonicalJson(const FString& Path, TArray<uint8>& OutBytes, TSharedPtr<FJsonObject>& OutObject, FString& OutFailure)
{
    if (!FFileHelper::LoadFileToArray(OutBytes, *Path) || OutBytes.Num() < 2)
    {
        OutFailure = TEXT("proof input cannot be read");
        return false;
    }
    if (OutBytes.Last() != '\n' || OutBytes[OutBytes.Num() - 2] == '\n' || OutBytes.Contains('\r') || OutBytes.Contains('\n'))
    {
        // A frozen canonical artifact has exactly one terminal LF and no raw
        // interior line break. JSON escape sequences remain ordinary bytes.
        int32 NewlineCount = 0;
        for (uint8 Byte : OutBytes)
        {
            NewlineCount += Byte == '\n' ? 1 : 0;
        }
        if (NewlineCount != 1 || OutBytes.Last() != '\n' || OutBytes.Contains('\r'))
        {
            OutFailure = TEXT("proof input violates exact LF serialization");
            return false;
        }
    }
    FUTF8ToTCHAR Converter(reinterpret_cast<const ANSICHAR*>(OutBytes.GetData()), OutBytes.Num() - 1);
    const FString Json(Converter.Length(), Converter.Get());
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
    if (!FJsonSerializer::Deserialize(Reader, OutObject) || !OutObject.IsValid())
    {
        OutFailure = TEXT("proof input is not JSON");
        return false;
    }
    return true;
}
}

AIntegratedUnrealProofAdapter::AIntegratedUnrealProofAdapter()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void AIntegratedUnrealProofAdapter::BeginPlay()
{
    Super::BeginPlay();
    FIntegratedUnrealMaterializationRecord Record;
    FString Failure;
    if (!LoadAndVerify(Record, Failure))
    {
        UE_LOG(LogCityMaterializationProof, Error, TEXT("Integrated Unreal proof refused materialization: %s"), *Failure);
        AddLabel(FVector(0.0f, 0.0f, 400.0f), FString::Printf(TEXT("INTEGRATED PROOF REFUSED\n%s"), *Failure), FColor::Red);
        return;
    }
    Materialize(Record);
    EmitAcceptanceReceipt(Record);
}

bool AIntegratedUnrealProofAdapter::LoadAndVerify(FIntegratedUnrealMaterializationRecord& OutRecord, FString& OutFailure) const
{
    FString PayloadPath;
    FString ReceiptPath;
    FString OutputDirectory;
    FString InteractionOpportunity;
    FString ProcessInstanceId;
    FParse::Value(FCommandLine::Get(), TEXT("IntegratedProofPayload="), PayloadPath);
    FParse::Value(FCommandLine::Get(), TEXT("IntegratedProofLaunchReceipt="), ReceiptPath);
    FParse::Value(FCommandLine::Get(), TEXT("IntegratedProofOutput="), OutputDirectory);
    FParse::Value(FCommandLine::Get(), TEXT("IntegratedProofInteractionOpportunity="), InteractionOpportunity);
    FParse::Value(FCommandLine::Get(), TEXT("IntegratedProofProcessInstanceId="), ProcessInstanceId);
    const FString CommandLine = FCommandLine::Get();
    if (PayloadPath.IsEmpty() || ReceiptPath.IsEmpty() || !IsAsciiNonEmpty(ProcessInstanceId) ||
        CommandLine.Contains(TEXT("CityProofRecord=")) || CommandLine.Contains(TEXT("CityProofExchange=")) || CommandLine.Contains(TEXT("CityProof=")))
    {
        OutFailure = TEXT("integrated proof input contract is incomplete or contains a legacy selector");
        return false;
    }

    TArray<uint8> PayloadBytes;
    TArray<uint8> ReceiptBytes;
    TSharedPtr<FJsonObject> Payload;
    TSharedPtr<FJsonObject> Receipt;
    if (!ReadStrictCanonicalJson(PayloadPath, PayloadBytes, Payload, OutFailure) || !ReadStrictCanonicalJson(ReceiptPath, ReceiptBytes, Receipt, OutFailure))
    {
        return false;
    }
    if (!HasExactKeys(Receipt, {TEXT("receipt_schema"), TEXT("artifact_role"), TEXT("raw_payload_sha256"), TEXT("expected_record_schema"), TEXT("expected_payload_schema"), TEXT("expected_scenario_id"), TEXT("expected_simulation_version")}) ||
        !Receipt->HasTypedField<EJson::String>(TEXT("raw_payload_sha256")) ||
        Receipt->GetStringField(TEXT("receipt_schema")) != LaunchReceiptSchema ||
        Receipt->GetStringField(TEXT("artifact_role")) != TEXT("canonical_materialization_input") ||
        Receipt->GetStringField(TEXT("raw_payload_sha256")) != Sha256Hex(PayloadBytes.GetData(), PayloadBytes.Num()) ||
        Receipt->GetStringField(TEXT("expected_record_schema")) != RecordSchema ||
        Receipt->GetStringField(TEXT("expected_payload_schema")) != PayloadSchema ||
        Receipt->GetStringField(TEXT("expected_scenario_id")) != ScenarioId ||
        Receipt->GetStringField(TEXT("expected_simulation_version")) != SimulationVersion)
    {
        OutFailure = TEXT("detached launch receipt does not bind this raw payload");
        return false;
    }
    if (!HasExactKeys(Payload, {TEXT("identity"), TEXT("current_causal_state"), TEXT("future_causal_state"), TEXT("causal_provenance")}) ||
        !Payload->HasTypedField<EJson::Object>(TEXT("identity")) || !Payload->HasTypedField<EJson::Object>(TEXT("current_causal_state")) ||
        !Payload->HasTypedField<EJson::Object>(TEXT("future_causal_state")) || !Payload->HasTypedField<EJson::Object>(TEXT("causal_provenance")))
    {
        OutFailure = TEXT("canonical payload does not have the exact envelope boundary");
        return false;
    }
    const TSharedPtr<FJsonObject> Identity = Payload->GetObjectField(TEXT("identity"));
    const TSharedPtr<FJsonObject> Current = Payload->GetObjectField(TEXT("current_causal_state"));
    const TSharedPtr<FJsonObject> Future = Payload->GetObjectField(TEXT("future_causal_state"));
    if (!HasExactKeys(Identity, {TEXT("record_schema"), TEXT("payload_schema"), TEXT("scenario_id"), TEXT("scenario_version"), TEXT("simulation_version"), TEXT("seed")}) ||
        Identity->GetStringField(TEXT("record_schema")) != RecordSchema || Identity->GetStringField(TEXT("payload_schema")) != PayloadSchema ||
        Identity->GetStringField(TEXT("scenario_id")) != ScenarioId || Identity->GetStringField(TEXT("scenario_version")) != TEXT("0.1.0") ||
        Identity->GetStringField(TEXT("simulation_version")) != SimulationVersion || Identity->GetStringField(TEXT("seed")) != TEXT("integrated-unreal-promotion-unload-repromotion-v1/0001") ||
        !HasExactKeys(Current, {TEXT("gate_token"), TEXT("commitments")}) || !Current->HasTypedField<EJson::Object>(TEXT("gate_token")) || !Current->HasTypedField<EJson::Object>(TEXT("commitments")) ||
        !HasExactKeys(Future, {TEXT("canonical_clock"), TEXT("unresolved_work")}))
    {
        OutFailure = TEXT("canonical payload identity or authoritative state is invalid");
        return false;
    }
    const TSharedPtr<FJsonObject> GateToken = Current->GetObjectField(TEXT("gate_token"));
    const TSharedPtr<FJsonObject> Commitments = Current->GetObjectField(TEXT("commitments"));
    if (!HasExactKeys(GateToken, {TEXT("state"), TEXT("physical_actor_id")}) || GateToken->GetStringField(TEXT("physical_actor_id")) != ActorId ||
        !HasExactKeys(Commitments, {TEXT("alpha")}) || !Commitments->HasTypedField<EJson::Object>(TEXT("alpha")))
    {
        OutFailure = TEXT("canonical payload gate token or alpha commitment is invalid");
        return false;
    }
    const TSharedPtr<FJsonObject> Alpha = Commitments->GetObjectField(TEXT("alpha"));
    if (!HasExactKeys(Alpha, {TEXT("state"), TEXT("terminal_disposition")}))
    {
        OutFailure = TEXT("canonical alpha representation is invalid");
        return false;
    }

    const FString GateState = GateToken->GetStringField(TEXT("state"));
    const FString AlphaState = Alpha->GetStringField(TEXT("state"));
    const FString Clock = Future->GetStringField(TEXT("canonical_clock"));
    const bool bSourceRecord = GateState == TEXT("enabled") && AlphaState == TEXT("active") && Clock == TEXT("t0/00");
    const bool bReturnRecord = Clock == TEXT("t1/00") && ((GateState == TEXT("disabled") && AlphaState == TEXT("failed_gate")) || (GateState == TEXT("enabled") && AlphaState == TEXT("succeeded")));
    if ((!bSourceRecord && !bReturnRecord) || (bSourceRecord && (OutputDirectory.IsEmpty() || InteractionOpportunity != SourceOpportunity)) ||
        (bReturnRecord && (!OutputDirectory.IsEmpty() || !InteractionOpportunity.IsEmpty())))
    {
        OutFailure = TEXT("payload stage and non-authoritative execution context disagree");
        return false;
    }

    OutRecord.CanonicalHash = Sha256Hex(PayloadBytes.GetData(), PayloadBytes.Num() - 1);
    OutRecord.RawPayloadHash = Sha256Hex(PayloadBytes.GetData(), PayloadBytes.Num());
    OutRecord.GateState = GateState;
    OutRecord.AlphaState = AlphaState;
    OutRecord.OutputDirectory = OutputDirectory;
    OutRecord.InteractionOpportunity = InteractionOpportunity;
    OutRecord.ProcessInstanceId = ProcessInstanceId;
    OutRecord.bProposalCapabilityEnabled = bSourceRecord;
    return true;
}

UStaticMeshComponent* AIntegratedUnrealProofAdapter::AddBlock(const FVector& Location, const FVector& Scale, const FLinearColor& Color, bool bBlocksMovement)
{
    UStaticMeshComponent* Block = NewObject<UStaticMeshComponent>(this);
    Block->SetupAttachment(SceneRoot);
    Block->SetStaticMesh(CubeMesh);
    Block->SetWorldLocation(Location);
    Block->SetWorldScale3D(Scale);
    Block->SetCollisionEnabled(bBlocksMovement ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    if (bBlocksMovement)
    {
        Block->SetCollisionProfileName(TEXT("BlockAll"));
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

UTextRenderComponent* AIntegratedUnrealProofAdapter::AddLabel(const FVector& Location, const FString& Text, const FColor& Color)
{
    UTextRenderComponent* Label = NewObject<UTextRenderComponent>(this);
    Label->SetupAttachment(SceneRoot);
    Label->SetWorldLocation(Location);
    Label->SetWorldRotation(FRotator(0.0f, 180.0f, 0.0f));
    Label->SetText(FText::FromString(Text));
    Label->SetTextRenderColor(Color);
    Label->SetWorldSize(54.0f);
    Label->SetHorizontalAlignment(EHTA_Center);
    Label->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Label->RegisterComponent();
    return Label;
}

void AIntegratedUnrealProofAdapter::Materialize(const FIntegratedUnrealMaterializationRecord& Record)
{
    AddBlock(FVector(0.0f, 0.0f, -10.0f), FVector(40.0f, 20.0f, 0.1f), FLinearColor(0.08f, 0.08f, 0.08f), true);
    AddLabel(FVector(-850.0f, -420.0f, 360.0f), FString::Printf(TEXT("INTEGRATED UNREAL LIFECYCLE\ncanonical: %s\ngate: %s | alpha: %s\nproposal capability: %s"), *Record.CanonicalHash.Left(12), *Record.GateState.ToUpper(), *Record.AlphaState.ToUpper(), Record.bProposalCapabilityEnabled ? TEXT("ENABLED") : TEXT("DISABLED")), FColor::White);
    if (AIntegratedGateTokenPoint* Gate = GetWorld()->SpawnActor<AIntegratedGateTokenPoint>(AIntegratedGateTokenPoint::StaticClass(), FVector(0.0f, 220.0f, 0.0f), FRotator::ZeroRotator))
    {
        Gate->Configure(Record.CanonicalHash, Record.RawPayloadHash, Record.OutputDirectory, Record.InteractionOpportunity, Record.GateState == TEXT("enabled"), Record.bProposalCapabilityEnabled);
    }
}

void AIntegratedUnrealProofAdapter::EmitAcceptanceReceipt(const FIntegratedUnrealMaterializationRecord& Record) const
{
    const FString Json = FString::Printf(
        TEXT("{\"accepted_canonical_hash\":\"%s\",\"accepted_raw_payload_sha256\":\"%s\",\"materialized_actor_id\":\"%s\",\"materialized_alpha_state\":\"%s\",\"materialized_gate_state\":\"%s\",\"process_instance_id\":\"%s\",\"proposal_capability_enabled\":%s,\"receipt_schema\":\"%s\"}"),
        *Record.CanonicalHash, *Record.RawPayloadHash, ActorId, *Record.AlphaState, *Record.GateState, *Record.ProcessInstanceId,
        Record.bProposalCapabilityEnabled ? TEXT("true") : TEXT("false"), AcceptanceReceiptSchema);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("INTEGRATED_MATERIALIZATION_RECEIPT:%s"), *Json);
}
