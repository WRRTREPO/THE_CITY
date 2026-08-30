#include "CrossDomainOccupancyLiveWorldProbe.h"

#include "CrossDomainOccupancyHeadAnchorActor.h"
#include "CrossDomainOccupancySubjectActor.h"
#include "Components/InputComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

namespace
{
constexpr TCHAR Scenario[] = TEXT("cross-domain-canonical-occupancy-materialization-v1");

TSharedPtr<FJsonValue> ObjectValue(const TSharedPtr<FJsonObject>& Value)
{
    return MakeShared<FJsonValueObject>(Value);
}

TArray<TSharedPtr<FJsonValue>> TagsOf(const AActor& Actor)
{
    TArray<FString> Tags;
    for (const FName Tag : Actor.Tags) Tags.Add(Tag.ToString());
    Tags.Sort();
    TArray<TSharedPtr<FJsonValue>> Result;
    for (const FString& Tag : Tags) Result.Add(MakeShared<FJsonValueString>(Tag));
    return Result;
}

bool HasPhase4Tag(const AActor& Actor)
{
    for (const FName Tag : Actor.Tags)
    {
        if (Tag.ToString().StartsWith(TEXT("cross_domain_occupancy/"))) return true;
    }
    return false;
}

bool HasRouteTag(const AActor& Actor)
{
    for (const FName Tag : Actor.Tags)
    {
        const FString Value = Tag.ToString();
        if (Value.StartsWith(TEXT("cross_domain_occupancy/")) && Value.Contains(TEXT("/route"))) return true;
    }
    return false;
}

TSharedPtr<FJsonObject> GenericActorRow(const AActor& Actor)
{
    TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
    Row->SetStringField(TEXT("actor_class"), Actor.GetClass()->GetPathName());
    Row->SetBoolField(TEXT("actor_has_begun_play"), Actor.HasActorBegunPlay());
    Row->SetBoolField(TEXT("actor_hidden"), Actor.IsHidden());
    Row->SetBoolField(TEXT("actor_is_being_destroyed"), Actor.IsActorBeingDestroyed());
    Row->SetBoolField(TEXT("actor_object_destroy_flags"), Actor.HasAnyFlags(RF_BeginDestroyed | RF_FinishDestroyed));
    Row->SetStringField(TEXT("actor_path"), Actor.GetPathName());
    Row->SetArrayField(TEXT("actor_tags"), TagsOf(Actor));
    return Row;
}

void SortRows(TArray<TSharedPtr<FJsonObject>>& Rows)
{
    Rows.Sort([](const TSharedPtr<FJsonObject>& Left, const TSharedPtr<FJsonObject>& Right)
    {
        FString A;
        FString B;
        Left->TryGetStringField(TEXT("actor_path"), A);
        Right->TryGetStringField(TEXT("actor_path"), B);
        return A < B;
    });
}

TArray<TSharedPtr<FJsonValue>> JsonRows(const TArray<TSharedPtr<FJsonObject>>& Rows)
{
    TArray<TSharedPtr<FJsonValue>> Result;
    for (const TSharedPtr<FJsonObject>& Row : Rows) Result.Add(ObjectValue(Row));
    return Result;
}
}

FCrossDomainOccupancyLiveWorldProbe::FCrossDomainOccupancyLiveWorldProbe(
    UWorld* InWorld,
    const FCDOImmutableProcessBinding& InBinding)
    : World(InWorld)
    , DomainRole(InBinding.DomainRole)
    , OperationalProcessInstanceId(InBinding.OperationalProcessInstanceId)
    , ProcessBindingRawSha256(InBinding.ProcessBindingRawSha256)
{
}

bool FCrossDomainOccupancyLiveWorldProbe::Stage(
    const FString& StageId,
    FCDOInjectedFaultPlan* FaultPlan,
    const TFunction<bool()>& Work,
    FString& OutReason,
    const TSharedPtr<FJsonObject>& OutputIdentity) const
{
    CrossDomainOccupancyRuntime::EmitStage(StageId, TEXT("entered"), TEXT(""), TEXT(""));
    if (CrossDomainOccupancyRuntime::InjectAt(FaultPlan, StageId, TEXT("before"), OutReason)) return false;
    if (!Work())
    {
        if (OutReason.IsEmpty()) OutReason = StageId + TEXT("_failed");
        return false;
    }
    CrossDomainOccupancyRuntime::EmitStage(StageId, TEXT("completed"), TEXT(""), TEXT(""), {}, OutputIdentity);
    if (CrossDomainOccupancyRuntime::InjectAt(FaultPlan, StageId, TEXT("after"), OutReason)) return false;
    return true;
}

bool FCrossDomainOccupancyLiveWorldProbe::InspectOnce(
    const FString& InspectionId,
    FCDOInjectedFaultPlan* FaultPlan,
    TSharedPtr<FJsonObject>& OutObservation,
    FString& OutReason) const
{
    UWorld* ExactWorld = nullptr;
    TArray<AActor*> ActorSlots;
    int32 LoadedLevelCount = 0;
    int32 LevelActorSlotCount = 0;
    int32 NullLevelActorSlotCount = 0;
    TArray<TSharedPtr<FJsonObject>> ProofRows;
    TArray<TSharedPtr<FJsonObject>> AnchorRows;
    TArray<TSharedPtr<FJsonObject>> SubjectRows;
    TArray<TSharedPtr<FJsonObject>> RouteRows;
    TArray<TSharedPtr<FJsonObject>> UnexpectedRows;
    TArray<TSharedPtr<FJsonObject>> PawnRows;
    TArray<TSharedPtr<FJsonObject>> ControllerRows;
    TArray<TSharedPtr<FJsonObject>> AutoInputRows;
    TArray<TSharedPtr<FJsonObject>> Phase4InputRows;
    FString ObservedGeneration;

    if (!Stage(TEXT("O02_verify_original_process_binding"), FaultPlan, [&]()
        {
            return (DomainRole == TEXT("domain_A") || DomainRole == TEXT("domain_B")) &&
                CrossDomainOccupancyJson::IsLowerSha256(OperationalProcessInstanceId) &&
                CrossDomainOccupancyJson::IsLowerSha256(ProcessBindingRawSha256);
        }, OutReason)) return false;

    if (!Stage(TEXT("O03_select_exact_process_bound_game_world"), FaultPlan, [&]()
        {
            ExactWorld = World.Get();
            return ExactWorld != nullptr && ExactWorld->WorldType == EWorldType::Game &&
                ExactWorld->GetOutermost()->GetName() == TEXT("/Engine/Maps/Entry");
        }, OutReason)) return false;

    if (!Stage(TEXT("O04_enumerate_all_loaded_level_actor_slots"), FaultPlan, [&]()
        {
            for (ULevel* Level : ExactWorld->GetLevels())
            {
                if (Level == nullptr) continue;
                ++LoadedLevelCount;
                for (const TObjectPtr<AActor>& Slot : Level->Actors)
                {
                    ++LevelActorSlotCount;
                    AActor* Actor = Slot.Get();
                    if (Actor == nullptr) ++NullLevelActorSlotCount;
                    else ActorSlots.Add(Actor);
                }
            }
            return LoadedLevelCount > 0 && LevelActorSlotCount >= ActorSlots.Num();
        }, OutReason)) return false;

    if (!Stage(TEXT("O05_classify_all_phase4_relevant_actor_rows"), FaultPlan, [&]()
        {
            for (AActor* Actor : ActorSlots)
            {
                if (ACrossDomainOccupancyHeadAnchorActor* Anchor = Cast<ACrossDomainOccupancyHeadAnchorActor>(Actor))
                {
                    TSharedPtr<FJsonObject> Row = Anchor->BuildLiveFieldRow();
                    AnchorRows.Add(Row);
                    ProofRows.Add(Row);
                    if (ObservedGeneration.IsEmpty()) ObservedGeneration = Anchor->GetPublicationGeneration();
                    else if (ObservedGeneration != Anchor->GetPublicationGeneration()) ObservedGeneration = TEXT("mixed");
                }
                else if (ACrossDomainOccupancySubjectActor* Subject = Cast<ACrossDomainOccupancySubjectActor>(Actor))
                {
                    TSharedPtr<FJsonObject> Row = Subject->BuildLiveFieldRow();
                    SubjectRows.Add(Row);
                    ProofRows.Add(Row);
                }
                else if (HasPhase4Tag(*Actor) || Actor->GetClass()->GetPathName().Contains(TEXT("CrossDomainOccupancy")))
                {
                    TSharedPtr<FJsonObject> Row = GenericActorRow(*Actor);
                    UnexpectedRows.Add(Row);
                    ProofRows.Add(Row);
                }
                if (HasRouteTag(*Actor)) RouteRows.Add(GenericActorRow(*Actor));
            }
            return true;
        }, OutReason)) return false;

    if (!Stage(TEXT("O06_inventory_all_pawn_controller_and_input_rows"), FaultPlan, [&]()
        {
            for (AActor* Actor : ActorSlots)
            {
                if (APawn* Pawn = Cast<APawn>(Actor))
                {
                    TSharedPtr<FJsonObject> Row = GenericActorRow(*Pawn);
                    AController* Controller = Pawn->GetController();
                    if (Controller == nullptr) Row->SetField(TEXT("controller_path"), MakeShared<FJsonValueNull>());
                    else Row->SetStringField(TEXT("controller_path"), Controller->GetPathName());
                    PawnRows.Add(Row);
                }
                if (AController* Controller = Cast<AController>(Actor))
                {
                    TSharedPtr<FJsonObject> Row = GenericActorRow(*Controller);
                    APawn* Pawn = Controller->GetPawn();
                    if (Pawn == nullptr) Row->SetField(TEXT("pawn_path"), MakeShared<FJsonValueNull>());
                    else Row->SetStringField(TEXT("pawn_path"), Pawn->GetPathName());
                    Row->SetBoolField(TEXT("possession_present"), Pawn != nullptr);
                    Row->SetBoolField(TEXT("input_enabled"), Controller->InputComponent != nullptr);
                    Row->SetBoolField(TEXT("phase_4_handler_reachable"), false);
                    ControllerRows.Add(Row);
                }
                if (Actor->AutoReceiveInput != EAutoReceiveInput::Disabled)
                {
                    TSharedPtr<FJsonObject> Row = GenericActorRow(*Actor);
                    Row->SetStringField(TEXT("auto_receive_input"), StaticEnum<EAutoReceiveInput::Type>()->GetNameStringByValue(Actor->AutoReceiveInput));
                    AutoInputRows.Add(Row);
                }
                const bool bPhase4Actor = Cast<ACrossDomainOccupancyHeadAnchorActor>(Actor) != nullptr ||
                    Cast<ACrossDomainOccupancySubjectActor>(Actor) != nullptr || HasPhase4Tag(*Actor);
                if (bPhase4Actor && Actor->InputComponent != nullptr)
                {
                    TSharedPtr<FJsonObject> Row = GenericActorRow(*Actor);
                    Row->SetStringField(TEXT("input_component_path"), Actor->InputComponent->GetPathName());
                    Row->SetStringField(TEXT("input_source"), TEXT("actor_input_component"));
                    Phase4InputRows.Add(Row);
                }
            }
            return true;
        }, OutReason)) return false;

    if (!Stage(TEXT("O07_sort_and_cross_check_counts_with_lists"), FaultPlan, [&]()
        {
            SortRows(ProofRows);
            SortRows(AnchorRows);
            SortRows(SubjectRows);
            SortRows(RouteRows);
            SortRows(UnexpectedRows);
            SortRows(PawnRows);
            SortRows(ControllerRows);
            SortRows(AutoInputRows);
            SortRows(Phase4InputRows);
            return ProofRows.Num() == AnchorRows.Num() + SubjectRows.Num() + UnexpectedRows.Num();
        }, OutReason)) return false;

    if (!Stage(TEXT("O08_construct_closed_live_observation"), FaultPlan, [&]()
        {
            OutObservation = MakeShared<FJsonObject>();
            OutObservation->SetNumberField(TEXT("anchor_actor_count"), AnchorRows.Num());
            OutObservation->SetArrayField(TEXT("anchor_actor_rows"), JsonRows(AnchorRows));
            OutObservation->SetNumberField(TEXT("auto_receive_input_actor_count"), AutoInputRows.Num());
            OutObservation->SetArrayField(TEXT("auto_receive_input_actor_rows"), JsonRows(AutoInputRows));
            OutObservation->SetNumberField(TEXT("controller_count"), ControllerRows.Num());
            OutObservation->SetArrayField(TEXT("controller_rows"), JsonRows(ControllerRows));
            OutObservation->SetStringField(TEXT("domain_role"), DomainRole);
            OutObservation->SetStringField(TEXT("inspection_id"), InspectionId);
            OutObservation->SetNumberField(TEXT("level_actor_slot_count"), LevelActorSlotCount);
            OutObservation->SetNumberField(TEXT("loaded_level_count"), LoadedLevelCount);
            OutObservation->SetNumberField(TEXT("null_level_actor_slot_count"), NullLevelActorSlotCount);
            OutObservation->SetStringField(TEXT("observation_schema"), TEXT("CrossDomainOccupancyLiveObservation.v1"));
            OutObservation->SetStringField(TEXT("observation_source"), TEXT("exhaustive_live_ue_world_census"));
            if (ObservedGeneration.IsEmpty()) OutObservation->SetField(TEXT("observed_publication_generation"), MakeShared<FJsonValueNull>());
            else OutObservation->SetStringField(TEXT("observed_publication_generation"), ObservedGeneration);
            OutObservation->SetStringField(TEXT("operational_process_instance_id"), OperationalProcessInstanceId);
            OutObservation->SetNumberField(TEXT("pawn_count"), PawnRows.Num());
            OutObservation->SetArrayField(TEXT("pawn_rows"), JsonRows(PawnRows));
            OutObservation->SetNumberField(TEXT("phase_4_actor_input_binding_count"), Phase4InputRows.Num());
            OutObservation->SetArrayField(TEXT("phase_4_actor_input_binding_rows"), JsonRows(Phase4InputRows));
            OutObservation->SetStringField(TEXT("process_binding_raw_sha256"), ProcessBindingRawSha256);
            OutObservation->SetNumberField(TEXT("proof_relevant_actor_count"), ProofRows.Num());
            OutObservation->SetArrayField(TEXT("proof_relevant_actor_rows"), JsonRows(ProofRows));
            OutObservation->SetStringField(TEXT("proof_scenario"), Scenario);
            OutObservation->SetNumberField(TEXT("route_actor_count"), RouteRows.Num());
            OutObservation->SetArrayField(TEXT("route_actor_rows"), JsonRows(RouteRows));
            OutObservation->SetNumberField(TEXT("subject_actor_count"), SubjectRows.Num());
            OutObservation->SetArrayField(TEXT("subject_actor_rows"), JsonRows(SubjectRows));
            OutObservation->SetNumberField(TEXT("unexpected_proof_tagged_actor_count"), UnexpectedRows.Num());
            OutObservation->SetArrayField(TEXT("unexpected_proof_tagged_actor_rows"), JsonRows(UnexpectedRows));
            OutObservation->SetStringField(TEXT("world_instance_identity"), FString::Printf(TEXT("%s@%p"), *ExactWorld->GetPathName(), ExactWorld));
            OutObservation->SetStringField(TEXT("world_package_name"), ExactWorld->GetOutermost()->GetName());
            OutObservation->SetStringField(TEXT("world_type"), TEXT("Game"));
            return true;
        }, OutReason)) return false;

    if (!Stage(TEXT("O09_emit_live_observation"), FaultPlan, []() { return true; }, OutReason, OutObservation)) return false;
    return true;
}
