#include "SimultaneousPhysicalRebindProbe.h"

#include "SimultaneousPhysicalDomainRepresentationActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Dom/JsonObject.h"
#include "EngineUtils.h"
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
    TSharedPtr<FJsonObject>& OutObservation,
    FString& OutReason) const
{
    if (!bBound || (InspectionId != TEXT("launch_physical_0001") && InspectionId != TEXT("refresh_physical_0001")))
    {
        OutReason = TEXT("immutable_binding_or_inspection_id_invalid");
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

    ASimultaneousPhysicalDomainRepresentationActor* Actor = Matching.Num() == 1 ? Matching[0] : nullptr;
    const UStaticMeshComponent* Mesh = Actor != nullptr ? Actor->GetPublishedRouteMesh() : nullptr;
    const UTextRenderComponent* Label = Actor != nullptr ? Actor->GetPublishedAccessLabel() : nullptr;
    const UMaterialInstanceDynamic* Material = Mesh != nullptr ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr;
    FLinearColor MeshColor(0, 0, 0, 0);
    const bool bColorRead = Material != nullptr && Material->GetVectorParameterValue(
        FMaterialParameterInfo(TEXT("Color")), MeshColor);
    const bool bActorHidden = Actor == nullptr || Actor->IsHidden();
    const bool bMeshRegistered = Mesh != nullptr && Mesh->IsRegistered();
    const bool bMeshVisible = bMeshRegistered && Mesh->IsVisible();
    const bool bLabelRegistered = Label != nullptr && Label->IsRegistered();
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
    FString ObservedState = TEXT("inconsistent");
    if (Matching.Num() == 1 && !bActorHidden && bMeshRegistered && bMeshVisible && bLabelRegistered && bLabelVisible)
    {
        if (bAvailableMesh && bAvailableLabel) ObservedState = TEXT("available");
        if (bBlockedMesh && bBlockedLabel) ObservedState = TEXT("blocked");
    }

    OutObservation = MakeShared<FJsonObject>();
    OutObservation->SetStringField(TEXT("observation_schema"), TEXT("SimultaneousPhysicalDomainPhysicalObservation.v1"));
    OutObservation->SetStringField(TEXT("proof_scenario"), TEXT("simultaneous-physical-domains-v1"));
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
