#include "CityMaterializationActor.h"

#include "BridgeAccessPoint.h"
#include "CrewOperationPoint.h"
#include "CityMaterializationProof.h"
#include "Components/SceneComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

ACityMaterializationActor::ACityMaterializationActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
}

void ACityMaterializationActor::BeginPlay()
{
    Super::BeginPlay();

    FCityProofRecord Record;
    FString Failure;
    if (!LoadAuthoritativeRecord(Record, Failure))
    {
        UE_LOG(LogCityMaterializationProof, Error, TEXT("City materialization proof refused to run: %s"), *Failure);
        AddLabel(FVector(0.0f, 0.0f, 450.0f), FString::Printf(TEXT("AUTHORITATIVE RECORD ERROR\n%s"), *Failure), FColor::Red);
        return;
    }

    Materialize(Record);
    UE_LOG(LogCityMaterializationProof, Display, TEXT("Materialized authoritative record %s (%s)."), *Record.RecordName, *Record.CanonicalHash);
}

bool ACityMaterializationActor::LoadAuthoritativeRecord(FCityProofRecord& OutRecord, FString& OutFailure) const
{
    FString RequestedRun = TEXT("Primary");
    FParse::Value(FCommandLine::Get(), TEXT("CityProof="), RequestedRun);
    FString ExplicitRecordPath;
    FParse::Value(FCommandLine::Get(), TEXT("CityProofRecord="), ExplicitRecordPath);
    RequestedRun = RequestedRun.Equals(TEXT("Counterfactual"), ESearchCase::IgnoreCase) ? TEXT("Counterfactual") : TEXT("Primary");

    const FString Filename = RequestedRun == TEXT("Counterfactual") ? TEXT("AshCrossingCounterfactual.json") : TEXT("AshCrossingPrimary.json");
    const FString Path = ExplicitRecordPath.IsEmpty() ? FPaths::ProjectContentDir() / TEXT("ProofRecords") / Filename : ExplicitRecordPath;
    FString Json;
    if (!FFileHelper::LoadFileToString(Json, *Path))
    {
        OutFailure = FString::Printf(TEXT("Cannot load %s"), *Path);
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        OutFailure = FString::Printf(TEXT("Invalid JSON in %s"), *Path);
        return false;
    }

    const FString RecordSchema = Root->HasField(TEXT("record_schema")) ? Root->GetStringField(TEXT("record_schema")) : TEXT("");
    OutRecord.RecordName = Root->GetStringField(TEXT("record_name"));
    OutRecord.CanonicalHash = Root->GetStringField(TEXT("canonical_sha256"));

    if (RecordSchema == TEXT("CrewDeploymentOpportunityRecord.v1"))
    {
        if (!Root->HasTypedField<EJson::Object>(TEXT("routes")) ||
            !Root->HasTypedField<EJson::Object>(TEXT("agents")) ||
            !Root->HasTypedField<EJson::Object>(TEXT("areas")) ||
            !Root->HasTypedField<EJson::Object>(TEXT("deployment")))
        {
            OutFailure = TEXT("Deployment record is missing canonical city sections.");
            return false;
        }

        const TSharedPtr<FJsonObject> Routes = Root->GetObjectField(TEXT("routes"));
        const TSharedPtr<FJsonObject> Agents = Root->GetObjectField(TEXT("agents"));
        const TSharedPtr<FJsonObject> Areas = Root->GetObjectField(TEXT("areas"));
        const TSharedPtr<FJsonObject> Deployment = Root->GetObjectField(TEXT("deployment"));
        if (!Routes->HasTypedField<EJson::Object>(TEXT("E_AB")) ||
            !Agents->HasTypedField<EJson::Object>(TEXT("police_unit_01")) ||
            !Areas->HasTypedField<EJson::Object>(TEXT("B")) ||
            !Areas->HasTypedField<EJson::Object>(TEXT("C")))
        {
            OutFailure = TEXT("Deployment record is missing its required bridge, police, or area facts.");
            return false;
        }

        const TSharedPtr<FJsonObject> Bridge = Routes->GetObjectField(TEXT("E_AB"));
        const TSharedPtr<FJsonObject> Police = Agents->GetObjectField(TEXT("police_unit_01"));
        const TSharedPtr<FJsonObject> AreaB = Areas->GetObjectField(TEXT("B"));
        const TSharedPtr<FJsonObject> AreaC = Areas->GetObjectField(TEXT("C"));
        OutRecord.bBridgeOpen = Bridge->GetBoolField(TEXT("open"));
        OutRecord.BridgeCapacity = Bridge->GetIntegerField(TEXT("capacity"));
        OutRecord.BridgeAccessPointState = Bridge->GetStringField(TEXT("bridge_access_point_state"));
        OutRecord.bCrewDeploymentOpportunityRecord = true;
        OutRecord.CrewInteractionDomain = Deployment->GetStringField(TEXT("interaction_domain"));
        OutRecord.bFireContainment = AreaB->GetBoolField(TEXT("fire_containment"));
        OutRecord.bCrewDisruption = AreaC->GetBoolField(TEXT("crew_disruption"));
        OutRecord.FireIntensity = AreaB->GetIntegerField(TEXT("fire_intensity"));
        OutRecord.PoliceLocation = Police->GetStringField(TEXT("location"));
        OutRecord.PoliceAvailability = Police->GetStringField(TEXT("availability"));
        OutRecord.PolicePresentAtDocklands = AreaC->GetIntegerField(TEXT("police_present"));
        OutRecord.DocklandsOwner = AreaC->GetStringField(TEXT("owner"));
        OutRecord.GangControl = AreaC->GetIntegerField(TEXT("gang_control"));
        OutRecord.RivalControl = AreaC->GetIntegerField(TEXT("rival_control"));
    }
    else if (RecordSchema == TEXT("BridgeAccessTraversalContentionRecord.v1"))
    {
        if (!Root->HasTypedField<EJson::Object>(TEXT("routes")) ||
            !Root->HasTypedField<EJson::Object>(TEXT("agents")) ||
            !Root->HasTypedField<EJson::Object>(TEXT("areas")))
        {
            OutFailure = TEXT("Contention record is missing canonical city sections.");
            return false;
        }

        const TSharedPtr<FJsonObject> Routes = Root->GetObjectField(TEXT("routes"));
        const TSharedPtr<FJsonObject> Agents = Root->GetObjectField(TEXT("agents"));
        const TSharedPtr<FJsonObject> Areas = Root->GetObjectField(TEXT("areas"));
        if (!Routes->HasTypedField<EJson::Object>(TEXT("E_AB")) ||
            !Agents->HasTypedField<EJson::Object>(TEXT("police_unit_01")) ||
            !Areas->HasTypedField<EJson::Object>(TEXT("B")) ||
            !Areas->HasTypedField<EJson::Object>(TEXT("C")))
        {
            OutFailure = TEXT("Contention record is missing its required bridge, police, or area facts.");
            return false;
        }

        const TSharedPtr<FJsonObject> Bridge = Routes->GetObjectField(TEXT("E_AB"));
        const TSharedPtr<FJsonObject> Police = Agents->GetObjectField(TEXT("police_unit_01"));
        const TSharedPtr<FJsonObject> AreaB = Areas->GetObjectField(TEXT("B"));
        const TSharedPtr<FJsonObject> AreaC = Areas->GetObjectField(TEXT("C"));
        OutRecord.bBridgeOpen = Bridge->GetBoolField(TEXT("open"));
        OutRecord.BridgeCapacity = Bridge->GetIntegerField(TEXT("capacity"));
        OutRecord.BridgeAccessPointState = Bridge->GetStringField(TEXT("bridge_access_point_state"));
        OutRecord.bBridgeAccessRoundTripRecord = true;
        OutRecord.bBridgeAccessContentionRecord = true;
        OutRecord.FireIntensity = AreaB->GetIntegerField(TEXT("fire_intensity"));
        OutRecord.PoliceLocation = Police->GetStringField(TEXT("location"));
        OutRecord.PoliceAvailability = Police->GetStringField(TEXT("availability"));
        OutRecord.PolicePresentAtDocklands = AreaC->GetIntegerField(TEXT("police_present"));
        OutRecord.DocklandsOwner = AreaC->GetStringField(TEXT("owner"));
        OutRecord.GangControl = AreaC->GetIntegerField(TEXT("gang_control"));
        OutRecord.RivalControl = AreaC->GetIntegerField(TEXT("rival_control"));
    }
    else
    {
        OutRecord.bBridgeOpen = Root->GetBoolField(TEXT("bridge_open"));
        OutRecord.BridgeCapacity = Root->HasField(TEXT("bridge_capacity")) ? Root->GetIntegerField(TEXT("bridge_capacity")) : (OutRecord.bBridgeOpen ? 1 : 0);
        OutRecord.BridgeAccessPointState = Root->HasField(TEXT("bridge_access_point_state"))
            ? Root->GetStringField(TEXT("bridge_access_point_state"))
            : TEXT("intact");
        OutRecord.bBridgeAccessRoundTripRecord = Root->HasField(TEXT("record_schema"));
        OutRecord.FireIntensity = Root->GetIntegerField(TEXT("fire_intensity"));
        OutRecord.PoliceLocation = Root->GetStringField(TEXT("police_location"));
        OutRecord.PoliceAvailability = Root->GetStringField(TEXT("police_availability"));
        OutRecord.PolicePresentAtDocklands = Root->GetIntegerField(TEXT("police_present_C"));
        OutRecord.DocklandsOwner = Root->GetStringField(TEXT("docklands_owner"));
        OutRecord.GangControl = Root->GetIntegerField(TEXT("gang_control"));
        OutRecord.RivalControl = Root->GetIntegerField(TEXT("rival_control"));
    }

    if ((OutRecord.DocklandsOwner == TEXT("gang") && OutRecord.PolicePresentAtDocklands != 0) ||
        (OutRecord.bBridgeOpen && OutRecord.FireIntensity >= 5) ||
        (OutRecord.bBridgeOpen && OutRecord.BridgeCapacity < 1) ||
        (OutRecord.bBridgeOpen && OutRecord.BridgeAccessPointState == TEXT("destroyed")) ||
        (OutRecord.BridgeAccessPointState == TEXT("destroyed") && OutRecord.BridgeCapacity != 0))
    {
        OutFailure = TEXT("Record violates frozen Ash Crossing facts.");
        return false;
    }

    return true;
}

void ACityMaterializationActor::SpawnBridgeAccessPoint(const FCityProofRecord& Record)
{
    if (!Record.bBridgeAccessRoundTripRecord)
    {
        return;
    }

    FString ExchangeDirectory = FPaths::ProjectSavedDir() / TEXT("RoundTripExchange");
    FParse::Value(FCommandLine::Get(), TEXT("CityProofExchange="), ExchangeDirectory);
    ABridgeAccessPoint* AccessPoint = GetWorld()->SpawnActor<ABridgeAccessPoint>(ABridgeAccessPoint::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    if (AccessPoint != nullptr)
    {
        AccessPoint->Configure(
            Record.CanonicalHash,
            ExchangeDirectory,
            Record.BridgeAccessPointState == TEXT("destroyed"),
            Record.bBridgeAccessContentionRecord);
    }
}

void ACityMaterializationActor::SpawnCrewOperationPoint(const FCityProofRecord& Record)
{
    if (!Record.bCrewDeploymentOpportunityRecord)
    {
        return;
    }

    FString ExchangeDirectory = FPaths::ProjectSavedDir() / TEXT("DeploymentOpportunityExchange");
    FParse::Value(FCommandLine::Get(), TEXT("CityProofExchange="), ExchangeDirectory);
    if (Record.CrewInteractionDomain == TEXT("B") && !Record.bFireContainment)
    {
        if (ACrewOperationPoint* Point = GetWorld()->SpawnActor<ACrewOperationPoint>(ACrewOperationPoint::StaticClass(), FVector(-220.0f, 420.0f, 0.0f), FRotator::ZeroRotator))
        {
            Point->Configure(Record.CanonicalHash, ExchangeDirectory, TEXT("B"), false);
        }
    }
    else if (Record.CrewInteractionDomain == TEXT("C") && !Record.bCrewDisruption)
    {
        if (ACrewOperationPoint* Point = GetWorld()->SpawnActor<ACrewOperationPoint>(ACrewOperationPoint::StaticClass(), FVector(1300.0f, 420.0f, 0.0f), FRotator::ZeroRotator))
        {
            Point->Configure(Record.CanonicalHash, ExchangeDirectory, TEXT("C"), false);
        }
    }
}

UStaticMeshComponent* ACityMaterializationActor::AddBlock(const FVector& Location, const FVector& Scale, const FLinearColor& Color, bool bBlocksMovement)
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

UTextRenderComponent* ACityMaterializationActor::AddLabel(const FVector& Location, const FString& Text, const FColor& Color)
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

void ACityMaterializationActor::Materialize(const FCityProofRecord& Record)
{
    const FLinearColor GroundColor(0.08f, 0.08f, 0.08f);
    const FLinearColor GangColor(0.75f, 0.05f, 0.05f);
    const FLinearColor PoliceColor(0.05f, 0.25f, 0.95f);
    const FLinearColor FireColor(0.95f, 0.24f, 0.02f);

    UPointLightComponent* KeyLight = NewObject<UPointLightComponent>(this, TEXT("ProofKeyLight"));
    KeyLight->SetupAttachment(SceneRoot);
    KeyLight->SetWorldLocation(FVector(-300.0f, -400.0f, 2200.0f));
    KeyLight->SetIntensity(180000.0f);
    KeyLight->SetAttenuationRadius(9000.0f);
    KeyLight->SetLightColor(FLinearColor(0.82f, 0.90f, 1.0f));
    KeyLight->RegisterComponent();

    UPointLightComponent* FillLight = NewObject<UPointLightComponent>(this, TEXT("ProofFireLight"));
    FillLight->SetupAttachment(SceneRoot);
    FillLight->SetWorldLocation(FVector(1200.0f, 300.0f, 900.0f));
    FillLight->SetIntensity(65000.0f);
    FillLight->SetAttenuationRadius(5000.0f);
    FillLight->SetLightColor(FireColor);
    FillLight->RegisterComponent();

    // The whole proof resolves onto one authoritative ground plane at Z = 0.
    // Every player pawn begins on this collision surface; there is no void below it.
    AddBlock(FVector(0.0f, 0.0f, -10.0f), FVector(70.0f, 30.0f, 0.1f), GroundColor, true);
    AddBlock(FVector(-1100.0f, 0.0f, 0.0f), FVector(10.0f, 2.2f, 0.12f), FLinearColor(0.25f, 0.25f, 0.25f), true);
    AddBlock(FVector(1100.0f, 0.0f, 0.0f), FVector(10.0f, 2.2f, 0.12f), FLinearColor(0.25f, 0.25f, 0.25f), true);

    const FString Status = FString::Printf(
        TEXT("ASH CROSSING — %s\nbridge: %s / capacity: %d | fire: %d\npolice: %s / %s\ndocklands: %s (%d / %d)\nrecord: %s"),
        *Record.RecordName,
        Record.bBridgeOpen ? TEXT("OPEN") : TEXT("CLOSED"),
        Record.BridgeCapacity,
        Record.FireIntensity,
        *Record.PoliceLocation,
        *Record.PoliceAvailability,
        *Record.DocklandsOwner,
        Record.GangControl,
        Record.RivalControl,
        *Record.CanonicalHash.Left(12));
    AddLabel(FVector(-1200.0f, -520.0f, 420.0f), Status, FColor::White);

    AddLabel(FVector(-1500.0f, 0.0f, 180.0f), TEXT("A — INLAND HUB"), FColor::White);
    AddLabel(FVector(0.0f, 0.0f, 300.0f), TEXT("B — ASH BRIDGE"), FColor::White);
    AddLabel(FVector(1500.0f, 0.0f, 300.0f), TEXT("C — DOCKLANDS YARD"), FColor::White);

    if (Record.bCrewDeploymentOpportunityRecord)
    {
        AddLabel(FVector(-1200.0f, 520.0f, 270.0f), FString::Printf(TEXT("ACTIVE CREW DOMAIN: %s\nphysical evidence only — canonical commit required"), *Record.CrewInteractionDomain), FColor::Cyan);
        if (Record.bFireContainment)
        {
            AddLabel(FVector(-220.0f, 420.0f, 260.0f), TEXT("FIRE CONTAINMENT: AUTHORITATIVE"), FColor::Green);
        }
        if (Record.bCrewDisruption)
        {
            AddLabel(FVector(1300.0f, 420.0f, 260.0f), TEXT("SEIZURE DISRUPTION: AUTHORITATIVE"), FColor::Green);
        }
    }

    if (Record.bBridgeOpen)
    {
        AddBlock(FVector(0.0f, 0.0f, 0.0f), FVector(3.5f, 2.2f, 0.12f), FLinearColor(0.3f, 0.3f, 0.3f), true);
        AddLabel(FVector(0.0f, 0.0f, 170.0f), TEXT("ROUTE OPEN"), FColor::Green);
    }
    else if (Record.BridgeAccessPointState == TEXT("destroyed"))
    {
        AddLabel(FVector(0.0f, 0.0f, 420.0f), TEXT("ACCESS DESTROYED - BRIDGE CLOSED"), FColor::Red);
    }
    else
    {
        AddBlock(FVector(0.0f, 0.0f, 170.0f), FVector(0.5f, 2.5f, 1.8f), FireColor, true);
        AddBlock(FVector(-70.0f, 0.0f, 40.0f), FVector(0.45f, 2.5f, 0.6f), GangColor, true);
        AddLabel(FVector(0.0f, 0.0f, 420.0f), TEXT("FIRE ACTIVE - BRIDGE CLOSED"), FColor::Red);
    }

    if (Record.DocklandsOwner == TEXT("gang"))
    {
        AddBlock(FVector(1500.0f, 0.0f, 100.0f), FVector(3.2f, 2.2f, 1.0f), GangColor, true);
        AddBlock(FVector(1300.0f, -320.0f, 80.0f), FVector(0.45f, 1.8f, 0.8f), GangColor, true);
        AddLabel(FVector(1500.0f, 0.0f, 360.0f), TEXT("GANG CONTROL — RIVAL DISPLACED"), FColor::Red);
    }
    else
    {
        AddBlock(FVector(1500.0f, 0.0f, 70.0f), FVector(2.6f, 2.2f, 0.7f), FLinearColor(0.35f, 0.35f, 0.35f), true);
        AddLabel(FVector(1500.0f, 0.0f, 300.0f), TEXT("CONTESTED — NO GANG CONTROL"), FColor::Yellow);
    }

    if (Record.PoliceLocation == TEXT("A"))
    {
        AddBlock(FVector(-1300.0f, 260.0f, 100.0f), FVector(0.5f, 0.5f, 1.0f), PoliceColor, true);
        AddLabel(FVector(-1300.0f, 260.0f, 260.0f), FString::Printf(TEXT("POLICE AT A - %s"), *Record.PoliceAvailability.ToUpper()), FColor::Blue);
    }
    else if (Record.PoliceLocation == TEXT("B"))
    {
        AddBlock(FVector(0.0f, 420.0f, 100.0f), FVector(0.5f, 0.5f, 1.0f), PoliceColor, true);
        AddLabel(FVector(0.0f, 420.0f, 260.0f), FString::Printf(TEXT("POLICE AT B - %s"), *Record.PoliceAvailability.ToUpper()), FColor::Blue);
    }
    else if (Record.PolicePresentAtDocklands > 0)
    {
        AddBlock(FVector(1700.0f, 260.0f, 100.0f), FVector(0.5f, 0.5f, 1.0f), PoliceColor, true);
        AddLabel(FVector(1700.0f, 260.0f, 260.0f), TEXT("POLICE PRESENT"), FColor::Blue);
    }

    SpawnBridgeAccessPoint(Record);
    SpawnCrewOperationPoint(Record);
}
