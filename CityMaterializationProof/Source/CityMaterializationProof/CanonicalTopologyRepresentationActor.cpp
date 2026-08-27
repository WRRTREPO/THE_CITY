#include "CanonicalTopologyRepresentationActor.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"

ACanonicalTopologyRepresentationActor::ACanonicalTopologyRepresentationActor()
{
    PrimaryActorTick.bCanEverTick = false;
    Shape = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RepresentationShape"));
    SetRootComponent(Shape);
    Shape->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
    Shape->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Shape->SetCanEverAffectNavigation(false);
}

void ACanonicalTopologyRepresentationActor::Configure(const FVector& Scale, const FLinearColor& Color)
{
    SetActorScale3D(Scale);
    if (UMaterialInterface* BaseMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
    {
        UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, this);
        Material->SetVectorParameterValue(TEXT("Color"), Color);
        Shape->SetMaterial(0, Material);
    }
}
