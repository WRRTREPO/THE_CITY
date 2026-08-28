#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SimultaneousPhysicalDomainRepresentationActor.generated.h"

class UMaterialInstanceDynamic;
class USceneComponent;
class UStaticMeshComponent;
class UTextRenderComponent;

// Disposable published route surface for Simultaneous Physical Domains v0.1.0.
// This Actor owns no canonical write, head, scheduling, evidence, or refresh
// authority.  Its getters exist only for the independent live-world probe.
UCLASS()
class CITYMATERIALIZATIONPROOF_API ASimultaneousPhysicalDomainRepresentationActor : public AActor
{
    GENERATED_BODY()

public:
    ASimultaneousPhysicalDomainRepresentationActor();

    bool PublishRepresentation(
        const FString& InDomainRole,
        const FString& InSiteId,
        const FString& InSiteSlot,
        const FString& InRouteId,
        const FString& InRouteSlot,
        const FString& InAccessState);

    const UStaticMeshComponent* GetPublishedRouteMesh() const { return RouteMesh; }
    const UTextRenderComponent* GetPublishedAccessLabel() const { return AccessLabel; }
    const UMaterialInstanceDynamic* GetPublishedRouteMaterial() const { return RouteMaterial; }
    const FString& GetPublishedDomainRole() const { return DomainRole; }
    const FString& GetPublishedAccessStateDiagnostic() const { return AccessStateDiagnostic; }

private:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> SiteMesh;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> RouteMesh;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UTextRenderComponent> SiteLabel;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UTextRenderComponent> AccessLabel;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> SiteMaterial;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> RouteMaterial;

    FString DomainRole;
    FString AccessStateDiagnostic;
};
