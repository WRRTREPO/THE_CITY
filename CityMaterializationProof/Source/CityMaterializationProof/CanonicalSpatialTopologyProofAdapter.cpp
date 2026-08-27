#include "CanonicalSpatialTopologyProofAdapter.h"

#include "CanonicalTopologyRepresentationActor.h"
#include "CityMaterializationProof.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "HAL/FileManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#include <openssl/sha.h>
#include <initializer_list>

namespace
{
constexpr TCHAR RecordSchema[] = TEXT("CanonicalResolutionEnvelope.v1");
constexpr TCHAR PayloadSchema[] = TEXT("CanonicalSpatialTopologyIdentityPayload.v1");
constexpr TCHAR ScenarioId[] = TEXT("canonical-spatial-topology-identity-v1");
constexpr TCHAR SimulationVersion[] = TEXT("0.7.0-draft.61");
constexpr TCHAR MapSchema[] = TEXT("CanonicalTopologyMaterializationMap.v1");
constexpr TCHAR ReceiptSchema[] = TEXT("CanonicalTopologyLaunchReceipt.v1");
constexpr TCHAR MaterializationReceiptSchema[] = TEXT("CanonicalTopologyMaterializationReceipt.v1");
constexpr TCHAR H0[] = TEXT("666d75281d3478e586edd12464d2736169f423c2d7b128bd3d2d2b1b2b826b29");
constexpr TCHAR H1[] = TEXT("78cc5ffe0c4758c296d8fee0bc2a95e230be0bec0a4aab680806eb670500804a");
constexpr TCHAR D0[] = TEXT("5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed");
constexpr TCHAR D1[] = TEXT("7ac7ece5c142ac4dee83abc6e83f7845d85dfc7f055ca6d678b7f04bdf1d795a");
constexpr TCHAR M0[] = TEXT("a1a45668e713b96d3ce52548596266320f2e58afe3b3102d6362ef655869305e");
constexpr TCHAR M1[] = TEXT("141da31e6033a5da24327be1688308cba2499ef51dc818a5eedd74a0f524dae9");
constexpr TCHAR L0[] = TEXT("e1dcd7814f33ec62f4265a86e2cc994157b5ae66a5af85a1e76ac721cbd12508");
constexpr TCHAR L1[] = TEXT("76998f2238e3edd46e6ced1309afe6c73660a0c8528ab2da5effa24fcb153f40");
constexpr TCHAR SiteA[] = TEXT("topology_site_0001");
constexpr TCHAR SiteB[] = TEXT("topology_site_0002");
constexpr TCHAR RouteId[] = TEXT("topology_route_0001");
constexpr TCHAR EndpointSemantics[] = TEXT("unordered_pair_fixture_only");
constexpr TCHAR R0MappingId[] = TEXT("topology_materialization_R0_0001");
constexpr TCHAR R1MappingId[] = TEXT("topology_materialization_R1_0001");

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

bool IsOperationalId(const FString& Value)
{
    if (Value.IsEmpty() || Value.Len() > 128)
    {
        return false;
    }
    for (TCHAR Character : Value)
    {
        const bool bAllowed = FChar::IsAlnum(Character) || Character == '.' || Character == '_' || Character == ':' || Character == '-';
        if (Character > 0x7f || !bAllowed)
        {
            return false;
        }
    }
    return true;
}

bool LoadExactStoredJson(const FString& Path, TArray<uint8>& OutBytes, FString& OutCanonical)
{
    if (!FFileHelper::LoadFileToArray(OutBytes, *Path) || OutBytes.Num() < 2 || OutBytes.Last() != '\n')
    {
        return false;
    }
    int32 NewlineCount = 0;
    for (uint8 Byte : OutBytes)
    {
        NewlineCount += Byte == '\n' ? 1 : 0;
        if (Byte == '\r')
        {
            return false;
        }
    }
    if (NewlineCount != 1)
    {
        return false;
    }
    FUTF8ToTCHAR Converter(reinterpret_cast<const ANSICHAR*>(OutBytes.GetData()), OutBytes.Num() - 1);
    OutCanonical = FString(Converter.Length(), Converter.Get());
    return true;
}

// Scan the token stream before constructing an FJsonObject.  A duplicate key
// is rejected at ingestion; UE's ordinary last-member-wins behavior never
// reaches the proof validator.
bool HasDuplicateObjectMember(const FString& Canonical)
{
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Canonical);
    TArray<TSet<FString>> ObjectKeyStack;
    EJsonNotation Notation;
    while (Reader->ReadNext(Notation))
    {
        const FString Identifier = Reader->GetIdentifier();
        if (!Identifier.IsEmpty() && ObjectKeyStack.Num() > 0)
        {
            TSet<FString>& Keys = ObjectKeyStack.Last();
            if (Keys.Contains(Identifier))
            {
                return true;
            }
            Keys.Add(Identifier);
        }
        if (Notation == EJsonNotation::ObjectStart)
        {
            ObjectKeyStack.AddDefaulted();
        }
        else if (Notation == EJsonNotation::ObjectEnd)
        {
            if (ObjectKeyStack.Num() == 0)
            {
                return true;
            }
            ObjectKeyStack.Pop();
        }
    }
    return ObjectKeyStack.Num() != 0 || !Reader->GetErrorMessage().IsEmpty();
}

bool ParseObjectAfterDuplicateScan(const FString& Canonical, TSharedPtr<FJsonObject>& OutObject)
{
    if (HasDuplicateObjectMember(Canonical))
    {
        return false;
    }
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Canonical);
    return FJsonSerializer::Deserialize(Reader, OutObject) && OutObject.IsValid();
}

bool HasExactKeys(const TSharedPtr<FJsonObject>& Object, std::initializer_list<const TCHAR*> Keys)
{
    if (!Object.IsValid() || Object->Values.Num() != static_cast<int32>(Keys.size()))
    {
        return false;
    }
    for (const TCHAR* Key : Keys)
    {
        if (!Object->HasField(Key))
        {
            return false;
        }
    }
    return true;
}

bool ExactString(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, const TCHAR* Expected)
{
    FString Value;
    return Object.IsValid() && Object->TryGetStringField(Field, Value) && Value == Expected;
}

bool NonEmptyString(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field)
{
    FString Value;
    return Object.IsValid() && Object->TryGetStringField(Field, Value) && !Value.IsEmpty();
}

bool ExactStringArray(const TArray<TSharedPtr<FJsonValue>>& Values, const TCHAR* First, const TCHAR* Second)
{
    FString A;
    FString B;
    return Values.Num() == 2 && Values[0].IsValid() && Values[1].IsValid() &&
        Values[0]->TryGetString(A) && Values[1]->TryGetString(B) && A == First && B == Second;
}
}

ACanonicalSpatialTopologyProofAdapter::ACanonicalSpatialTopologyProofAdapter()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void ACanonicalSpatialTopologyProofAdapter::BeginPlay()
{
    Super::BeginPlay();
    FCanonicalTopologyMaterializationRecord Record;
    FString Stage;
    FString Reason;
    if (!LoadAndVerify(Record, Stage, Reason))
    {
        EmitFailure(Stage, Reason);
        return;
    }
    if (!Materialize(Record, Stage, Reason))
    {
        UE_LOG(LogCityMaterializationProof, Error,
            TEXT("CANONICAL_TOPOLOGY_OPERATIONAL_MATERIALIZATION_FAILURE:{\"canonical_write_attempted\":false,\"reason_code\":\"representation_spawn_failed\"}"));
        return;
    }
    EmitMaterializationReceipt(Record);
}

bool ACanonicalSpatialTopologyProofAdapter::LoadAndVerify(FCanonicalTopologyMaterializationRecord& OutRecord, FString& OutStage, FString& OutReason) const
{
    FString InputRoot;
    FString ProcessInstanceId;
    FParse::Value(FCommandLine::Get(), TEXT("CanonicalTopologyProofInputRoot="), InputRoot);
    FParse::Value(FCommandLine::Get(), TEXT("CanonicalTopologyProofProcessInstanceId="), ProcessInstanceId);
    const FString CommandLine(FCommandLine::Get());
    if (InputRoot.IsEmpty() || !IsOperationalId(ProcessInstanceId) ||
        CommandLine.Contains(TEXT("CanonicalTopologyProofBranch=")) || CommandLine.Contains(TEXT("CanonicalTopologyProofAccess=")) ||
        CommandLine.Contains(TEXT("CanonicalTopologyProofEndpoint=")) || CommandLine.Contains(TEXT("CanonicalTopologyProofMappingId=")) ||
        CommandLine.Contains(TEXT("IntegratedProof")) || CommandLine.Contains(TEXT("ConcurrentEvidence")) ||
        CommandLine.Contains(TEXT("CityProof=")) || CommandLine.Contains(TEXT("CityProofRecord=")) || CommandLine.Contains(TEXT("CityProofExchange=")))
    {
        OutStage = TEXT("input_inventory");
        OutReason = TEXT("unexpected_input_file");
        return false;
    }

    TArray<FString> Entries;
    IFileManager::Get().FindFiles(Entries, *(FPaths::Combine(InputRoot, TEXT("*"))), true, true);
    Entries.Sort();
    const TArray<FString> ExpectedEntries = {TEXT("canonical_payload.json"), TEXT("launch_receipt.json"), TEXT("materialization_map.json")};
    if (Entries != ExpectedEntries)
    {
        OutStage = TEXT("input_inventory");
        OutReason = Entries.Num() < 3 ? TEXT("missing_input_file") : TEXT("unexpected_input_file");
        return false;
    }

    TArray<uint8> ReceiptBytes;
    FString ReceiptCanonical;
    if (!LoadExactStoredJson(FPaths::Combine(InputRoot, TEXT("launch_receipt.json")), ReceiptBytes, ReceiptCanonical))
    {
        OutStage = TEXT("launch_receipt");
        OutReason = TEXT("invalid_launch_receipt");
        return false;
    }
    TSharedPtr<FJsonObject> Receipt;
    if (!ParseObjectAfterDuplicateScan(ReceiptCanonical, Receipt) || !HasExactKeys(Receipt, {
        TEXT("receipt_schema"), TEXT("canonical_payload_raw_sha256"), TEXT("materialization_map_raw_sha256"),
        TEXT("expected_canonical_hash"), TEXT("expected_record_schema"), TEXT("expected_payload_schema"),
        TEXT("expected_scenario_id"), TEXT("expected_simulation_version"), TEXT("expected_mapping_schema"), TEXT("expected_mapping_id")
    }) || !ExactString(Receipt, TEXT("receipt_schema"), ReceiptSchema) ||
        !NonEmptyString(Receipt, TEXT("canonical_payload_raw_sha256")) ||
        !NonEmptyString(Receipt, TEXT("materialization_map_raw_sha256")) ||
        !NonEmptyString(Receipt, TEXT("expected_canonical_hash")) ||
        !NonEmptyString(Receipt, TEXT("expected_record_schema")) ||
        !NonEmptyString(Receipt, TEXT("expected_payload_schema")) ||
        !NonEmptyString(Receipt, TEXT("expected_scenario_id")) ||
        !NonEmptyString(Receipt, TEXT("expected_simulation_version")) ||
        !NonEmptyString(Receipt, TEXT("expected_mapping_schema")) ||
        !NonEmptyString(Receipt, TEXT("expected_mapping_id")))
    {
        OutStage = TEXT("launch_receipt");
        OutReason = TEXT("invalid_launch_receipt");
        return false;
    }
    const FString RawReceiptHash = Sha256Hex(ReceiptBytes.GetData(), ReceiptBytes.Num());
    const bool bReceiptR0 = RawReceiptHash == L0;
    const bool bReceiptR1 = RawReceiptHash == L1;
    if (!bReceiptR0 && !bReceiptR1)
    {
        OutStage = TEXT("launch_receipt");
        OutReason = TEXT("launch_receipt_hash_mismatch");
        return false;
    }

    TArray<uint8> PayloadBytes;
    TArray<uint8> MapBytes;
    FString PayloadCanonical;
    FString MapCanonical;
    if (!LoadExactStoredJson(FPaths::Combine(InputRoot, TEXT("canonical_payload.json")), PayloadBytes, PayloadCanonical) ||
        !LoadExactStoredJson(FPaths::Combine(InputRoot, TEXT("materialization_map.json")), MapBytes, MapCanonical))
    {
        OutStage = TEXT("raw_hash");
        OutReason = TEXT("artifact_raw_hash_mismatch");
        return false;
    }
    const FString RawPayloadHash = Sha256Hex(PayloadBytes.GetData(), PayloadBytes.Num());
    const FString RawMapHash = Sha256Hex(MapBytes.GetData(), MapBytes.Num());
    const TCHAR* ExpectedPayloadRawHash = bReceiptR0 ? D0 : D1;
    const TCHAR* ExpectedMapRawHash = bReceiptR0 ? M0 : M1;
    if (RawPayloadHash != ExpectedPayloadRawHash || RawMapHash != ExpectedMapRawHash ||
        !ExactString(Receipt, TEXT("canonical_payload_raw_sha256"), *RawPayloadHash) ||
        !ExactString(Receipt, TEXT("materialization_map_raw_sha256"), *RawMapHash))
    {
        OutStage = TEXT("raw_hash");
        OutReason = TEXT("artifact_raw_hash_mismatch");
        return false;
    }

    FTCHARToUTF8 PayloadUtf8(*PayloadCanonical);
    const FString CanonicalHash = Sha256Hex(reinterpret_cast<const uint8*>(PayloadUtf8.Get()), PayloadUtf8.Length());
    const bool bR0 = bReceiptR0 && CanonicalHash == H0;
    const bool bR1 = bReceiptR1 && CanonicalHash == H1;
    if (!bR0 && !bR1)
    {
        OutStage = TEXT("payload_validation");
        OutReason = TEXT("invalid_canonical_payload");
        return false;
    }

    TSharedPtr<FJsonObject> Payload;
    TSharedPtr<FJsonObject> Map;
    if (!ParseObjectAfterDuplicateScan(PayloadCanonical, Payload) || !ParseObjectAfterDuplicateScan(MapCanonical, Map))
    {
        OutStage = TEXT("parse");
        OutReason = TEXT("json_parse_failure");
        return false;
    }
    if (!HasExactKeys(Payload, {TEXT("identity"), TEXT("current_causal_state"), TEXT("future_causal_state"), TEXT("causal_provenance")}))
    {
        OutStage = TEXT("payload_validation");
        OutReason = TEXT("invalid_canonical_payload");
        return false;
    }
    const TSharedPtr<FJsonObject>* Identity = nullptr;
    const TSharedPtr<FJsonObject>* Current = nullptr;
    const TSharedPtr<FJsonObject>* Topology = nullptr;
    const TSharedPtr<FJsonObject>* Sites = nullptr;
    const TSharedPtr<FJsonObject>* Routes = nullptr;
    const TSharedPtr<FJsonObject>* Route = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* EndpointValues = nullptr;
    FString EndpointSiteId0;
    FString EndpointSiteId1;
    if (!Payload->TryGetObjectField(TEXT("identity"), Identity) || !Payload->TryGetObjectField(TEXT("current_causal_state"), Current) ||
        !(*Current)->TryGetObjectField(TEXT("spatial_topology"), Topology) || !(*Topology)->TryGetObjectField(TEXT("sites"), Sites) ||
        !(*Topology)->TryGetObjectField(TEXT("routes"), Routes) || !(*Routes)->TryGetObjectField(RouteId, Route) ||
        !(*Route)->TryGetArrayField(TEXT("endpoint_site_ids"), EndpointValues) ||
        !HasExactKeys(*Identity, {TEXT("record_schema"), TEXT("payload_schema"), TEXT("scenario_id"), TEXT("scenario_version"), TEXT("simulation_version"), TEXT("seed")}) ||
        !ExactString(*Identity, TEXT("record_schema"), RecordSchema) || !ExactString(*Identity, TEXT("payload_schema"), PayloadSchema) ||
        !ExactString(*Identity, TEXT("scenario_id"), ScenarioId) || !ExactString(*Identity, TEXT("simulation_version"), SimulationVersion) ||
        !HasExactKeys(*Sites, {SiteA, SiteB}) || !(*Sites)->TryGetField(SiteA)->IsNull() || !(*Sites)->TryGetField(SiteB)->IsNull() ||
        !HasExactKeys(*Routes, {RouteId}) || !HasExactKeys(*Route, {TEXT("access_state"), TEXT("endpoint_semantics"), TEXT("endpoint_site_ids")}) ||
        !ExactStringArray(*EndpointValues, SiteA, SiteB) || !ExactString(*Route, TEXT("endpoint_semantics"), EndpointSemantics) ||
        !ExactString(*Route, TEXT("access_state"), bR0 ? TEXT("available") : TEXT("blocked")))
    {
        OutStage = TEXT("payload_validation");
        OutReason = TEXT("invalid_canonical_payload");
        return false;
    }
    if (!(*EndpointValues)[0]->TryGetString(EndpointSiteId0) || !(*EndpointValues)[1]->TryGetString(EndpointSiteId1))
    {
        OutStage = TEXT("payload_validation");
        OutReason = TEXT("invalid_canonical_payload");
        return false;
    }

    const TSharedPtr<FJsonObject>* MapSites = nullptr;
    const TSharedPtr<FJsonObject>* MapRoutes = nullptr;
    const TCHAR* ExpectedMappingId = bR0 ? R0MappingId : R1MappingId;
    if (!HasExactKeys(Map, {TEXT("mapping_schema"), TEXT("mapping_id"), TEXT("source_canonical_hash"), TEXT("sites"), TEXT("routes")}) ||
        !ExactString(Map, TEXT("mapping_schema"), MapSchema) || !ExactString(Map, TEXT("mapping_id"), ExpectedMappingId) ||
        !ExactString(Map, TEXT("source_canonical_hash"), *CanonicalHash) || !Map->TryGetObjectField(TEXT("sites"), MapSites) ||
        !Map->TryGetObjectField(TEXT("routes"), MapRoutes) || !HasExactKeys(*MapSites, {SiteA, SiteB}) ||
        !ExactString(*MapSites, *EndpointSiteId0, TEXT("representation_site_slot_01")) || !ExactString(*MapSites, *EndpointSiteId1, TEXT("representation_site_slot_02")) ||
        !HasExactKeys(*MapRoutes, {RouteId}) || !ExactString(*MapRoutes, RouteId, TEXT("representation_route_slot_01")))
    {
        OutStage = TEXT("map_validation");
        OutReason = TEXT("invalid_materialization_map");
        return false;
    }

    if (!ExactString(Receipt, TEXT("expected_canonical_hash"), *CanonicalHash) ||
        !ExactString(Receipt, TEXT("expected_record_schema"), RecordSchema) ||
        !ExactString(Receipt, TEXT("expected_payload_schema"), PayloadSchema) ||
        !ExactString(Receipt, TEXT("expected_scenario_id"), ScenarioId) ||
        !ExactString(Receipt, TEXT("expected_simulation_version"), SimulationVersion) ||
        !ExactString(Receipt, TEXT("expected_mapping_schema"), MapSchema) ||
        !ExactString(Receipt, TEXT("expected_mapping_id"), ExpectedMappingId))
    {
        OutStage = TEXT("cross_artifact_binding");
        OutReason = TEXT("cross_artifact_binding_mismatch");
        return false;
    }

    OutRecord.CanonicalHash = CanonicalHash;
    OutRecord.RawPayloadHash = RawPayloadHash;
    OutRecord.RawMapHash = RawMapHash;
    OutRecord.MappingId = ExpectedMappingId;
    OutRecord.AccessState = bR0 ? TEXT("available") : TEXT("blocked");
    OutRecord.CanonicalRouteId = RouteId;
    OutRecord.EndpointSiteId0 = EndpointSiteId0;
    OutRecord.EndpointSiteId1 = EndpointSiteId1;
    OutRecord.ProcessInstanceId = ProcessInstanceId;
    return true;
}

UStaticMeshComponent* ACanonicalSpatialTopologyProofAdapter::AddLocalBlock(const FVector& Location, const FVector& Scale, const FLinearColor& Color)
{
    UStaticMeshComponent* Block = NewObject<UStaticMeshComponent>(this);
    Block->SetupAttachment(SceneRoot);
    Block->SetStaticMesh(CubeMesh);
    Block->SetWorldLocation(Location);
    Block->SetWorldScale3D(Scale);
    Block->SetCollisionProfileName(TEXT("BlockAll"));
    Block->SetCanEverAffectNavigation(false);
    if (ShapeMaterial != nullptr)
    {
        UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(ShapeMaterial, this);
        Material->SetVectorParameterValue(TEXT("Color"), Color);
        Block->SetMaterial(0, Material);
    }
    Block->RegisterComponent();
    return Block;
}

UTextRenderComponent* ACanonicalSpatialTopologyProofAdapter::AddLocalLabel(const FVector& Location, const FString& Text, const FColor& Color)
{
    UTextRenderComponent* Label = NewObject<UTextRenderComponent>(this);
    Label->SetupAttachment(SceneRoot);
    Label->SetWorldLocation(Location);
    Label->SetWorldRotation(FRotator(0.0f, 180.0f, 0.0f));
    Label->SetText(FText::FromString(Text));
    Label->SetTextRenderColor(Color);
    Label->SetWorldSize(42.0f);
    Label->SetHorizontalAlignment(EHTA_Center);
    Label->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Label->RegisterComponent();
    return Label;
}

bool ACanonicalSpatialTopologyProofAdapter::Materialize(const FCanonicalTopologyMaterializationRecord& Record, FString& OutStage, FString& OutReason)
{
    FActorSpawnParameters SiteAParams;
    SiteAParams.Name = TEXT("TopologySiteSlot01");
    SiteAParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    SiteAParams.bDeferConstruction = true;
    FActorSpawnParameters SiteBParams;
    SiteBParams.Name = TEXT("TopologySiteSlot02");
    SiteBParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    SiteBParams.bDeferConstruction = true;
    FActorSpawnParameters RouteParams;
    RouteParams.Name = TEXT("TopologyRouteSlot01");
    RouteParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    RouteParams.bDeferConstruction = true;
    const FTransform SiteTransform01(FRotator::ZeroRotator, FVector(-320.0f, 180.0f, 70.0f));
    const FTransform SiteTransform02(FRotator::ZeroRotator, FVector(320.0f, 180.0f, 70.0f));
    const FTransform RouteTransform(FRotator::ZeroRotator, FVector(0.0f, 180.0f, 40.0f));
    ACanonicalTopologyRepresentationActor* NewSiteActor01 = GetWorld()->SpawnActor<ACanonicalTopologyRepresentationActor>(ACanonicalTopologyRepresentationActor::StaticClass(), SiteTransform01, SiteAParams);
    ACanonicalTopologyRepresentationActor* NewSiteActor02 = GetWorld()->SpawnActor<ACanonicalTopologyRepresentationActor>(ACanonicalTopologyRepresentationActor::StaticClass(), SiteTransform02, SiteBParams);
    ACanonicalTopologyRepresentationActor* NewRouteActor01 = GetWorld()->SpawnActor<ACanonicalTopologyRepresentationActor>(ACanonicalTopologyRepresentationActor::StaticClass(), RouteTransform, RouteParams);
    if (NewSiteActor01 == nullptr || NewSiteActor02 == nullptr || NewRouteActor01 == nullptr)
    {
        if (NewSiteActor01 != nullptr)
        {
            NewSiteActor01->Destroy();
        }
        if (NewSiteActor02 != nullptr)
        {
            NewSiteActor02->Destroy();
        }
        if (NewRouteActor01 != nullptr)
        {
            NewRouteActor01->Destroy();
        }
        OutStage = TEXT("payload_validation");
        OutReason = TEXT("invalid_canonical_payload");
        return false;
    }
    NewSiteActor01->SetActorHiddenInGame(true);
    NewSiteActor02->SetActorHiddenInGame(true);
    NewRouteActor01->SetActorHiddenInGame(true);
    NewSiteActor01->FinishSpawning(SiteTransform01);
    NewSiteActor02->FinishSpawning(SiteTransform02);
    NewRouteActor01->FinishSpawning(RouteTransform);
    SiteActor01 = NewSiteActor01;
    SiteActor02 = NewSiteActor02;
    RouteActor01 = NewRouteActor01;
    SiteActor01->Configure(FVector(0.8f, 0.8f, 1.2f), FLinearColor(0.15f, 0.45f, 0.95f));
    SiteActor02->Configure(FVector(0.8f, 0.8f, 1.2f), FLinearColor(0.15f, 0.45f, 0.95f));
    RouteActor01->Configure(FVector(6.4f, 0.28f, 0.16f), Record.AccessState == TEXT("available") ? FLinearColor(0.1f, 0.85f, 0.35f) : FLinearColor(0.9f, 0.12f, 0.12f));
    SiteActor01->SetActorHiddenInGame(false);
    SiteActor02->SetActorHiddenInGame(false);
    RouteActor01->SetActorHiddenInGame(false);
    UPointLightComponent* Light = NewObject<UPointLightComponent>(this);
    Light->SetupAttachment(SceneRoot);
    Light->SetWorldLocation(FVector(-400.0f, -400.0f, 1200.0f));
    Light->SetIntensity(180000.0f);
    Light->SetAttenuationRadius(6000.0f);
    Light->RegisterComponent();
    AddLocalBlock(FVector(0.0f, 0.0f, -40.0f), FVector(30.0f, 18.0f, 0.4f), FLinearColor(0.08f, 0.10f, 0.14f));
    AddLocalLabel(FVector(-320.0f, 180.0f, 260.0f), Record.EndpointSiteId0, FColor::White);
    AddLocalLabel(FVector(320.0f, 180.0f, 260.0f), Record.EndpointSiteId1, FColor::White);
    AddLocalLabel(FVector(0.0f, 180.0f, 330.0f), FString::Printf(TEXT("%s\n%s\n%s"), *Record.CanonicalRouteId, EndpointSemantics, *Record.AccessState.ToUpper()), Record.AccessState == TEXT("available") ? FColor::Green : FColor::Red);
    return true;
}

void ACanonicalSpatialTopologyProofAdapter::EmitMaterializationReceipt(const FCanonicalTopologyMaterializationRecord& Record) const
{
    const FString Json = FString::Printf(
        TEXT("{\"accepted_canonical_hash\":\"%s\",\"accepted_canonical_payload_raw_sha256\":\"%s\",\"accepted_mapping_id\":\"%s\",\"accepted_materialization_map_raw_sha256\":\"%s\",\"materialized_access_state\":\"%s\",\"materialized_canonical_route_id\":\"%s\",\"materialized_canonical_site_ids\":[\"%s\",\"%s\"],\"materialized_endpoint_site_ids\":[\"%s\",\"%s\"],\"operational_actor_instance_ids\":{\"representation_route_slot_01\":\"%s\",\"representation_site_slot_01\":\"%s\",\"representation_site_slot_02\":\"%s\"},\"operational_process_instance_id\":\"%s\",\"receipt_schema\":\"%s\"}"),
        *Record.CanonicalHash, *Record.RawPayloadHash, *Record.MappingId, *Record.RawMapHash, *Record.AccessState,
        *Record.CanonicalRouteId, *Record.EndpointSiteId0, *Record.EndpointSiteId1, *Record.EndpointSiteId0, *Record.EndpointSiteId1, *RouteActor01->GetFName().ToString(), *SiteActor01->GetFName().ToString(),
        *SiteActor02->GetFName().ToString(), *Record.ProcessInstanceId, MaterializationReceiptSchema);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("CANONICAL_TOPOLOGY_MATERIALIZATION_RECEIPT:%s"), *Json);
}

void ACanonicalSpatialTopologyProofAdapter::EmitFailure(const FString& Stage, const FString& Reason) const
{
    const FString Json = FString::Printf(
        TEXT("{\"canonical_write_attempted\":false,\"diagnostic_schema\":\"CanonicalTopologyMaterializationFailure.v1\",\"materialization_started\":false,\"reason_code\":\"%s\",\"stage\":\"%s\"}"),
        *Reason, *Stage);
    UE_LOG(LogCityMaterializationProof, Error, TEXT("CANONICAL_TOPOLOGY_MATERIALIZATION_FAILURE:%s"), *Json);
}
