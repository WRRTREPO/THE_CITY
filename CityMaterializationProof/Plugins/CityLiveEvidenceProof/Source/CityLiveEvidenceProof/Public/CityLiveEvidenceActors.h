#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include <initializer_list>
#include "CityLiveEvidenceActors.generated.h"

class FJsonObject;
class FJsonValue;
class ACityLiveEvidenceGameMode;

namespace CityLCER
{
    CITYLIVEEVIDENCEPROOF_API FString Digest(const FString& Bytes);
    CITYLIVEEVIDENCEPROOF_API FString Canonical(const TSharedPtr<FJsonValue>& Value);
    CITYLIVEEVIDENCEPROOF_API FString Stored(const TSharedPtr<FJsonObject>& Object);
    CITYLIVEEVIDENCEPROOF_API bool Parse(const FString& Raw, TSharedPtr<FJsonObject>& Object);
    CITYLIVEEVIDENCEPROOF_API bool Keys(const TSharedPtr<FJsonObject>& Object, std::initializer_list<const TCHAR*> Names);
}

UCLASS(Abstract)
class CITYLIVEEVIDENCEPROOF_API ACityLiveEvidenceActor : public AActor
{
    GENERATED_BODY()

public:
    ACityLiveEvidenceActor();
    const FString& GetEvidenceRole() const { return Role; }
    const FString& GetEvidenceDomain() const { return Domain; }
    const FString& GetRecordRawSha256() const { return RawSha256; }
    int32 GetEvidenceGeneration() const { return Generation; }
    const FString& GetAllocationOwner() const { return AllocationOwner; }

protected:
    FString Role;
    FString Domain;
    FString RawSha256;
    FString AllocationOwner;
    FString AcceptedRecordRaw;
    int32 Generation = -1;

private:
    friend class ACityLiveEvidenceGameMode;
    bool Configure(const FString& InRole, const FString& InDomain, const FString& RecordRaw, int32 InGeneration);
};

UCLASS()
class CITYLIVEEVIDENCEPROOF_API ACityLiveEvidenceHeadAnchor final : public ACityLiveEvidenceActor
{
    GENERATED_BODY()
};

UCLASS()
class CITYLIVEEVIDENCEPROOF_API ACityLiveEvidenceResource final : public ACityLiveEvidenceActor
{
    GENERATED_BODY()

private:
    friend class ACityLiveEvidenceGameMode;
    bool Interact(const TSharedPtr<FJsonObject>& Routing, TSharedPtr<FJsonObject>& Result);
    void DisableProposals();
    int32 InteractionCounter = 0;
    bool bProposalCapability = true;
};

namespace CityLCER
{
    CITYLIVEEVIDENCEPROOF_API bool Exact(const FString& Left, const FString& Right);
    CITYLIVEEVIDENCEPROOF_API bool Less(const FString& Left, const FString& Right);
    CITYLIVEEVIDENCEPROOF_API bool Contains(const TArray<FString>& Values, const FString& Value);
    CITYLIVEEVIDENCEPROOF_API void AddUnique(TArray<FString>& Values, const FString& Value);
}
