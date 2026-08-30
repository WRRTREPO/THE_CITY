#pragma once

#include "CoreMinimal.h"
#include "CrossDomainOccupancyCommandRouter.h"

class ACrossDomainOccupancyHeadAnchorActor;
class ACrossDomainOccupancySubjectActor;
class FJsonObject;
class FJsonValue;
class UWorld;

struct FCDOCandidateValues
{
    FString DomainRole;
    FString CanonicalPayloadRawSha256;
    FString CanonicalHash;
    FString ProjectionRawSha256;
    FString ProjectionId;
    FString ProjectedSiteId;
    FString SiteSlot;
    FString SubjectSlot;
    FString OccupancyKind;
    FString OccupancyReference;
    FString LocalDisposition;
    FString PublicationGeneration;
    FString Operation;
    FString OperationId;
    FString OperationInvocationRawSha256;
    bool bSubjectRequired = false;
};

struct FCDOInputFileWitness
{
    FString Filename;
    FString Realpath;
    FString RawSha256;
    uint64 Device = 0;
    uint64 Inode = 0;
    int64 Size = 0;
    TArray<uint8> Bytes;
};

// Exact payload+projection+invocation validator and disposable world publisher.
// It owns no canonical scheduler, resolver, head observer, guard, or peer state.
class CITYMATERIALIZATIONPROOF_API FCrossDomainOccupancyProofAdapter final
{
public:
    FCrossDomainOccupancyProofAdapter(UWorld* InWorld, const FCDOImmutableProcessBinding& InBinding);

    bool MaterializeOnce(
        const FString& OperationId,
        const FString& RelativeBundleRoot,
        const FString& CommandRawSha256,
        FCDOInjectedFaultPlan* FaultPlan,
        TSharedPtr<FJsonObject>& OutReceipt,
        FString& OutReason);

    const FString& GetRepresentedCanonicalHash() const { return RepresentedCanonicalHash; }
    const FString& GetPublicationGeneration() const { return PublicationGeneration; }
    const FString& GetPublicationState() const { return PublicationState; }
    void MarkInvalid() { PublicationState = TEXT("invalid"); }

private:
    bool Stage(
        const FString& StageId,
        FCDOInjectedFaultPlan* FaultPlan,
        const TFunction<bool()>& Work,
        FString& OutReason,
        const TArray<TSharedPtr<FJsonValue>>& InputRows = {},
        const TSharedPtr<FJsonObject>& OutputIdentity = nullptr) const;
    bool InventoryBundle(
        const FString& OperationId,
        const FString& RelativeBundleRoot,
        int& OutDirectoryDescriptor,
        TArray<FCDOInputFileWitness>& OutFiles,
        FString& OutReason) const;
    bool ReadBundleFile(
        int DirectoryDescriptor,
        FCDOInputFileWitness& File,
        FString& OutReason) const;
    bool ValidateCandidateInputs(
        const FString& OperationId,
        const TArray<FCDOInputFileWitness>& Files,
        FCDOCandidateValues& OutCandidate,
        FString& OutReason) const;
    bool DestroyPredecessorGeneration(FString& OutReason);
    bool SpawnSubject(const FCDOCandidateValues& Candidate, FString& OutReason);
    bool SpawnAnchor(const FCDOCandidateValues& Candidate, FString& OutReason);
    bool ValidatePublishedGeneration(const FCDOCandidateValues& Candidate, FString& OutReason) const;
    TSharedPtr<FJsonObject> BuildReceipt(
        const FCDOCandidateValues& Candidate,
        const FString& CommandRawSha256,
        bool bPrivateCandidate = false) const;

    TWeakObjectPtr<UWorld> World;
    FCDOImmutableProcessBinding Binding;
    TWeakObjectPtr<ACrossDomainOccupancyHeadAnchorActor> PublishedAnchor;
    TWeakObjectPtr<ACrossDomainOccupancySubjectActor> PublishedSubject;
    FString RepresentedCanonicalHash;
    FString PublicationGeneration;
    FString PublicationState = TEXT("none");
};
