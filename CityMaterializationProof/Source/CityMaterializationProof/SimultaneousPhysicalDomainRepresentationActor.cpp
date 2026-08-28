#include "SimultaneousPhysicalDomainRepresentationActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
constexpr TCHAR SiteA[] = TEXT("topology_site_0001");
constexpr TCHAR SiteB[] = TEXT("topology_site_0002");
constexpr TCHAR RouteId[] = TEXT("topology_route_0001");

bool ExactRoleProjection(
    const FString& DomainRole,
    const FString& SiteId,
    const FString& SiteSlot,
    const FString& RouteSlot)
{
    if (DomainRole == TEXT("domain_A"))
    {
        return SiteId == SiteA && SiteSlot == TEXT("domain_A_site_slot_01") &&
            RouteSlot == TEXT("domain_A_route_slot_01");
    }
    if (DomainRole == TEXT("domain_B"))
    {
        return SiteId == SiteB && SiteSlot == TEXT("domain_B_site_slot_01") &&
            RouteSlot == TEXT("domain_B_route_slot_01");
    }
    return false;
}
}

ASimultaneousPhysicalDomainRepresentationActor::ASimultaneousPhysicalDomainRepresentationActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    SiteMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PublishedSiteMesh"));
    SiteMesh->SetupAttachment(SceneRoot);
    SiteMesh->SetRelativeLocation(FVector(-180.0, 0.0, 55.0));
    SiteMesh->SetRelativeScale3D(FVector(1.6, 1.6, 1.1));
    SiteMesh->SetCanEverAffectNavigation(false);
    SiteMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    RouteMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PublishedRouteMesh"));
    RouteMesh->SetupAttachment(SceneRoot);
    RouteMesh->SetRelativeLocation(FVector(80.0, 0.0, 42.0));
    RouteMesh->SetRelativeScale3D(FVector(3.4, 0.28, 0.28));
    RouteMesh->SetCanEverAffectNavigation(false);
    RouteMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UMaterialInterface* BasicMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    SiteMesh->SetStaticMesh(Cube);
    RouteMesh->SetStaticMesh(Cube);
    if (BasicMaterial != nullptr)
    {
        SiteMaterial = UMaterialInstanceDynamic::Create(BasicMaterial, this);
        RouteMaterial = UMaterialInstanceDynamic::Create(BasicMaterial, this);
        SiteMesh->SetMaterial(0, SiteMaterial);
        RouteMesh->SetMaterial(0, RouteMaterial);
    }

    SiteLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PublishedSiteLabel"));
    SiteLabel->SetupAttachment(SceneRoot);
    SiteLabel->SetRelativeLocation(FVector(-180.0, 0.0, 155.0));
    SiteLabel->SetHorizontalAlignment(EHTA_Center);
    SiteLabel->SetWorldSize(30.0f);

    AccessLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PublishedAccessLabel"));
    AccessLabel->SetupAttachment(SceneRoot);
    AccessLabel->SetRelativeLocation(FVector(80.0, 0.0, 110.0));
    AccessLabel->SetHorizontalAlignment(EHTA_Center);
    AccessLabel->SetWorldSize(32.0f);
}

bool ASimultaneousPhysicalDomainRepresentationActor::PublishRepresentation(
    const FString& InDomainRole,
    const FString& InSiteId,
    const FString& InSiteSlot,
    const FString& InRouteId,
    const FString& InRouteSlot,
    const FString& InAccessState)
{
    if (!ExactRoleProjection(InDomainRole, InSiteId, InSiteSlot, InRouteSlot) ||
        InRouteId != RouteId || (InAccessState != TEXT("available") && InAccessState != TEXT("blocked")) ||
        RouteMaterial == nullptr || SiteMaterial == nullptr)
    {
        return false;
    }

    DomainRole = InDomainRole;
    AccessStateDiagnostic = InAccessState;
    Tags.Reset();
    Tags.Add(FName(*FString::Printf(TEXT("simultaneous_physical_domain/%s/%s"), *InDomainRole, *InRouteSlot)));

    const bool bAvailable = InAccessState == TEXT("available");
    const FLinearColor RouteColor = bAvailable
        ? FLinearColor(0.10f, 0.85f, 0.35f, 1.00f)
        : FLinearColor(0.90f, 0.12f, 0.12f, 1.00f);
    RouteMaterial->SetVectorParameterValue(TEXT("Color"), RouteColor);
    SiteMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.12f, 0.35f, 0.85f, 1.00f));
    AccessLabel->SetText(FText::FromString(bAvailable ? TEXT("AVAILABLE") : TEXT("BLOCKED")));
    AccessLabel->SetTextRenderColor(bAvailable ? FColor(0, 255, 0, 255) : FColor(255, 0, 0, 255));
    SiteLabel->SetText(FText::FromString(InSiteId));
    SiteLabel->SetTextRenderColor(FColor(125, 185, 255, 255));

    SetActorHiddenInGame(false);
    SiteMesh->SetVisibility(true, true);
    RouteMesh->SetVisibility(true, true);
    SiteLabel->SetVisibility(true, true);
    AccessLabel->SetVisibility(true, true);
    return true;
}
