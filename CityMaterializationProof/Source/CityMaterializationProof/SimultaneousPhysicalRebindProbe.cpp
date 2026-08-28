#include "SimultaneousPhysicalRebindProbe.h"

#include "SimultaneousPhysicalDomainRepresentationActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Dom/JsonObject.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
TSharedPtr<FJsonValue> NumberValue(double Value)
{
    return MakeShared<FJsonValueNumber>(Value);
}
}

ASimultaneousPhysicalRebindProbe::ASimultaneousPhysicalRebindProbe()
{
    PrimaryActorTick.bCanEverTick = false;
}

bool ASimultaneousPhysicalRebindProbe::BindProcessIdentity(const FSPDImmutableProcessBinding& Binding)
{
    if (bBound || (Binding.DomainRole != TEXT("domain_A") && Binding.DomainRole != TEXT("domain_B")) ||
        !SimultaneousPhysicalDomainJson::IsLowerSha256(Binding.OperationalProcessInstanceId) ||
        !SimultaneousPhysicalDomainJson::IsLowerSha256(Binding.ProcessBindingRawSha256))
    {
        return false;
    }
    DomainRole = Binding.DomainRole;
    OperationalProcessInstanceId = Binding.OperationalProcessInstanceId;
    ProcessBindingRawSha256 = Binding.ProcessBindingRawSha256;
    const FString RouteSlot = DomainRole == TEXT("domain_A")
        ? TEXT("domain_A_route_slot_01") : TEXT("domain_B_route_slot_01");
    ProbeTag = FString::Printf(TEXT("simultaneous_physical_domain/%s/%s"), *DomainRole, *RouteSlot);
    bBound = true;
    return true;
}

bool ASimultaneousPhysicalRebindProbe::InspectPublishedRoute(
    const FString& InspectionId,
    FSPDInjectedFaultPlan* FaultPlan,
    TSharedPtr<FJsonObject>& OutObservation,
    FString& OutReason) const
{
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("immutable_process_binding_verification"), TEXT("at"), OutReason))
    {
        return false;
    }
    if (!bBound || (InspectionId != TEXT("launch_physical_0001") && InspectionId != TEXT("refresh_physical_0001")))
    {
        OutReason = TEXT("immutable_binding_or_inspection_id_invalid");
        return false;
    }
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("role_probe_tag_derivation"), TEXT("at"), OutReason))
    {
        return false;
    }
    const FString ExpectedRouteSlot = DomainRole == TEXT("domain_A")
        ? TEXT("domain_A_route_slot_01") : TEXT("domain_B_route_slot_01");
    const FString ExpectedProbeTag = FString::Printf(
        TEXT("simultaneous_physical_domain/%s/%s"), *DomainRole, *ExpectedRouteSlot);
    if (ProbeTag != ExpectedProbeTag)
    {
        OutReason = TEXT("role_probe_tag_derivation_failed");
        return false;
    }

    int32 PlayerControllerCount = 0;
    int32 PlayerControllerWithPawnCount = 0;
    int32 PawnCount = 0;
    int32 Phase3InputPathCount = 0;
    for (TActorIterator<APlayerController> It(GetWorld()); It; ++It)
    {
        ++PlayerControllerCount;
        if (It->GetPawn() != nullptr)
        {
            ++PlayerControllerWithPawnCount;
        }
    }
    for (TActorIterator<APawn> It(GetWorld()); It; ++It)
    {
        ++PawnCount;
    }
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor* Candidate = *It;
        if (Candidate != nullptr && Candidate->GetClass()->GetName().StartsWith(TEXT("SimultaneousPhysical")) &&
            (Candidate->AutoReceiveInput != EAutoReceiveInput::Disabled || Candidate->InputComponent != nullptr))
        {
            ++Phase3InputPathCount;
        }
    }
    if (PlayerControllerCount != 1 || PlayerControllerWithPawnCount != 0 ||
        PawnCount != 0 || Phase3InputPathCount != 0)
    {
        OutReason = FString::Printf(
            TEXT("phase3_player_input_isolation_failed_pc_%d_possessed_%d_pawn_%d_input_%d"),
            PlayerControllerCount, PlayerControllerWithPawnCount, PawnCount, Phase3InputPathCount);
        return false;
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("live_world_actor_enumeration"), TEXT("at"), OutReason))
    {
        return false;
    }
    TArray<ASimultaneousPhysicalDomainRepresentationActor*> Matching;
    for (TActorIterator<ASimultaneousPhysicalDomainRepresentationActor> It(GetWorld()); It; ++It)
    {
        ASimultaneousPhysicalDomainRepresentationActor* Actor = *It;
        if (Actor != nullptr && !Actor->IsActorBeingDestroyed() && Actor->ActorHasTag(FName(*ProbeTag)))
        {
            Matching.Add(Actor);
        }
    }

    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("exact_actor_count_check"), TEXT("at"), OutReason))
    {
        return false;
    }
    ASimultaneousPhysicalDomainRepresentationActor* Actor = Matching.Num() == 1 ? Matching[0] : nullptr;
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("live_mesh_component_lookup"), TEXT("at"), OutReason))
    {
        return false;
    }
    const UStaticMeshComponent* Mesh = Actor != nullptr ? Actor->GetPublishedRouteMesh() : nullptr;
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("live_mesh_visibility_and_material_parameter_read"), TEXT("at"), OutReason))
    {
        return false;
    }
    const UMaterialInstanceDynamic* Material = Mesh != nullptr ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr;
    FLinearColor MeshColor(0, 0, 0, 0);
    const bool bColorRead = Material != nullptr && Material->GetVectorParameterValue(
        FMaterialParameterInfo(TEXT("Color")), MeshColor);
    const bool bActorHidden = Actor == nullptr || Actor->IsHidden();
    const bool bMeshRegistered = Mesh != nullptr && Mesh->IsRegistered();
    const bool bMeshVisible = bMeshRegistered && Mesh->IsVisible();
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("live_label_component_lookup"), TEXT("at"), OutReason))
    {
        return false;
    }
    const UTextRenderComponent* Label = Actor != nullptr ? Actor->GetPublishedAccessLabel() : nullptr;
    const bool bLabelRegistered = Label != nullptr && Label->IsRegistered();
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("live_label_visibility_text_and_color_read"), TEXT("at"), OutReason))
    {
        return false;
    }
    const bool bLabelVisible = bLabelRegistered && Label->IsVisible();
    const FString LabelText = Label != nullptr ? Label->Text.ToString() : TEXT("");
    const FColor LabelColor = Label != nullptr ? Label->TextRenderColor : FColor(0, 0, 0, 0);

    auto Near = [](float A, float B) { return FMath::Abs(A - B) <= 0.000001f; };
    const bool bAvailableMesh = bColorRead && Near(MeshColor.R, 0.10f) && Near(MeshColor.G, 0.85f) &&
        Near(MeshColor.B, 0.35f) && Near(MeshColor.A, 1.00f);
    const bool bBlockedMesh = bColorRead && Near(MeshColor.R, 0.90f) && Near(MeshColor.G, 0.12f) &&
        Near(MeshColor.B, 0.12f) && Near(MeshColor.A, 1.00f);
    const bool bAvailableLabel = LabelText == TEXT("AVAILABLE") && LabelColor == FColor(0, 255, 0, 255);
    const bool bBlockedLabel = LabelText == TEXT("BLOCKED") && LabelColor == FColor(255, 0, 0, 255);
    if (SimultaneousPhysicalDomainFault::InjectAt(
        FaultPlan, TEXT("physical_observation"), TEXT("independent_surface_consistency_classification"), TEXT("at"), OutReason))
    {
        return false;
    }
    FString ObservedState = TEXT("inconsistent");
    if (Matching.Num() == 1 && !bActorHidden && bMeshRegistered && bMeshVisible && bLabelRegistered && bLabelVisible)
    {
        if (bAvailableMesh && bAvailableLabel) ObservedState = TEXT("available");
        if (bBlockedMesh && bBlockedLabel) ObservedState = TEXT("blocked");
    }

    OutObservation = MakeShared<FJsonObject>();
    OutObservation->SetStringField(TEXT("observation_schema"), TEXT("SimultaneousPhysicalDomainPhysicalObservation.v1"));
    OutObservation->SetStringField(TEXT("proof_scenario"), TEXT("simultaneous-physical-domains-v1.1"));
    OutObservation->SetStringField(TEXT("domain_role"), DomainRole);
    OutObservation->SetStringField(TEXT("operational_process_instance_id"), OperationalProcessInstanceId);
    OutObservation->SetStringField(TEXT("process_binding_raw_sha256"), ProcessBindingRawSha256);
    OutObservation->SetStringField(TEXT("inspection_id"), InspectionId);
    OutObservation->SetStringField(TEXT("probe_tag"), ProbeTag);
    OutObservation->SetNumberField(TEXT("matching_live_actor_count"), Matching.Num());
    OutObservation->SetStringField(TEXT("actor_class"), TEXT("ASimultaneousPhysicalDomainRepresentationActor"));
    OutObservation->SetBoolField(TEXT("actor_hidden_in_game"), bActorHidden);
    OutObservation->SetBoolField(TEXT("route_mesh_registered"), bMeshRegistered);
    OutObservation->SetBoolField(TEXT("route_mesh_visible"), bMeshVisible);
    OutObservation->SetArrayField(TEXT("observed_route_mesh_color_parameter_rgba"), {
        NumberValue(MeshColor.R), NumberValue(MeshColor.G), NumberValue(MeshColor.B), NumberValue(MeshColor.A)
    });
    OutObservation->SetBoolField(TEXT("access_label_registered"), bLabelRegistered);
    OutObservation->SetBoolField(TEXT("access_label_visible"), bLabelVisible);
    OutObservation->SetStringField(TEXT("observed_access_label_text"), LabelText);
    OutObservation->SetArrayField(TEXT("observed_access_label_color_rgba8"), {
        NumberValue(LabelColor.R), NumberValue(LabelColor.G), NumberValue(LabelColor.B), NumberValue(LabelColor.A)
    });
    OutObservation->SetStringField(TEXT("observed_physical_access_state"), ObservedState);
    OutObservation->SetStringField(TEXT("observation_source"), TEXT("live_ue_world_actor_component_inspection"));
    return true;
}
