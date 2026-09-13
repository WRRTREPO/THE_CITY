#include "CityLiveEvidenceActors.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/World.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include <openssl/sha.h>

namespace CityLCER
{
bool Exact(const FString& Left, const FString& Right)
{
    if (Left.Len() != Right.Len()) return false;
    for (int32 Index = 0; Index < Left.Len(); ++Index)
        if (Left[Index] != Right[Index]) return false;
    return true;
}

static uint32 NextCodePoint(const FString& Text, int32& Index)
{
    uint32 Point = static_cast<uint32>(Text[Index++]);
    if (Point >= 0xd800 && Point <= 0xdbff && Index < Text.Len())
    {
        const uint32 Low = static_cast<uint32>(Text[Index]);
        if (Low >= 0xdc00 && Low <= 0xdfff)
        {
            ++Index;
            Point = 0x10000 + ((Point - 0xd800) << 10) + (Low - 0xdc00);
        }
    }
    return Point;
}

bool Less(const FString& Left, const FString& Right)
{
    int32 LeftIndex = 0;
    int32 RightIndex = 0;
    while (LeftIndex < Left.Len() && RightIndex < Right.Len())
    {
        const uint32 LeftPoint = NextCodePoint(Left, LeftIndex);
        const uint32 RightPoint = NextCodePoint(Right, RightIndex);
        if (LeftPoint != RightPoint) return LeftPoint < RightPoint;
    }
    return LeftIndex == Left.Len() && RightIndex < Right.Len();
}

bool Contains(const TArray<FString>& Values, const FString& Value)
{
    for (const FString& Item : Values) if (Exact(Item, Value)) return true;
    return false;
}

void AddUnique(TArray<FString>& Values, const FString& Value)
{
    if (!Contains(Values, Value)) Values.Add(Value);
}

FString Digest(const FString& Bytes)
{
    FTCHARToUTF8 Utf8(*Bytes);
    uint8 Hash[SHA256_DIGEST_LENGTH];
    SHA256(reinterpret_cast<const uint8*>(Utf8.Get()), Utf8.Length(), Hash);
    FString Result;
    for (uint8 Byte : Hash) Result += FString::Printf(TEXT("%02x"), Byte);
    return Result;
}

static FString Quote(const FString& Text)
{
    FString Result = TEXT("\"");
    for (TCHAR Character : Text)
    {
        switch (Character)
        {
        case '"': Result += TEXT("\\\""); break;
        case '\\': Result += TEXT("\\\\"); break;
        case '\b': Result += TEXT("\\b"); break;
        case '\f': Result += TEXT("\\f"); break;
        case '\n': Result += TEXT("\\n"); break;
        case '\r': Result += TEXT("\\r"); break;
        case '\t': Result += TEXT("\\t"); break;
        default:
            if (Character < 0x20 || Character > 0x7e)
                Result += FString::Printf(TEXT("\\u%04x"), static_cast<uint32>(Character));
            else Result.AppendChar(Character);
        }
    }
    return Result + TEXT("\"");
}

FString Canonical(const TSharedPtr<FJsonValue>& Value)
{
    if (!Value.IsValid()) return FString();
    switch (Value->Type)
    {
    case EJson::Null: return TEXT("null");
    case EJson::Boolean: return Value->AsBool() ? TEXT("true") : TEXT("false");
    case EJson::String: return Quote(Value->AsString());
    case EJson::Number:
    {
        const double Number = Value->AsNumber();
        // All frozen runtime numbers are integral. Reject lossy/nonfinite input.
        if (!FMath::IsFinite(Number) || Number != FMath::FloorToDouble(Number) || FMath::Abs(Number) > 9007199254740991.0)
            return FString();
        return FString::Printf(TEXT("%.0f"), Number == 0 ? 0.0 : Number);
    }
    case EJson::Array:
    {
        TArray<FString> Parts;
        for (const auto& Item : Value->AsArray())
        {
            FString Part = Canonical(Item);
            if (Part.IsEmpty()) return FString();
            Parts.Add(MoveTemp(Part));
        }
        return TEXT("[") + FString::Join(Parts, TEXT(",")) + TEXT("]");
    }
    case EJson::Object:
    {
        const auto Object = Value->AsObject();
        if (!Object.IsValid()) return FString();
        TArray<FString> Names;
        for (const auto& Entry : Object->Values) Names.Add(FString(Entry.Key.ToView()));
        Names.Sort(CityLCER::Less);
        TArray<FString> Parts;
        for (const FString& Name : Names)
        {
            FString Part = Canonical(Object->TryGetField(Name));
            if (Part.IsEmpty()) return FString();
            Parts.Add(Quote(Name) + TEXT(":") + Part);
        }
        return TEXT("{") + FString::Join(Parts, TEXT(",")) + TEXT("}");
    }
    default: return FString();
    }
}

FString Stored(const TSharedPtr<FJsonObject>& Object)
{
    const FString Body = Canonical(MakeShared<FJsonValueObject>(Object));
    return Body.IsEmpty() ? FString() : Body + TEXT("\n");
}

bool Parse(const FString& Raw, TSharedPtr<FJsonObject>& Object)
{
    Object.Reset();
    if (!Raw.EndsWith(TEXT("\n")) || Raw.EndsWith(TEXT("\n\n"))) return false;
    const auto Reader = TJsonReaderFactory<>::Create(Raw);
    // Re-encoding detects duplicate keys, whitespace, escapes and trailing data.
    return FJsonSerializer::Deserialize(Reader, Object, FJsonSerializer::EFlags::None) && Object.IsValid() && CityLCER::Exact(Stored(Object), Raw);
}

bool Keys(const TSharedPtr<FJsonObject>& Object, std::initializer_list<const TCHAR*> Names)
{
    if (!Object.IsValid() || Object->Values.Num() != static_cast<int32>(Names.size())) return false;
    TArray<FString> Matched;
    for (const TCHAR* Name : Names)
    {
        const FString Expected(Name);
        if (Contains(Matched, Expected)) return false;
        bool Found = false;
        for (const auto& Entry : Object->Values)
            if (Exact(FString(Entry.Key.ToView()), Expected)) { Found = true; break; }
        if (!Found) return false;
        Matched.Add(Expected);
    }
    return true;
}
}

ACityLiveEvidenceActor::ACityLiveEvidenceActor()
{
    PrimaryActorTick.bCanEverTick = false;
    AutoReceiveInput = EAutoReceiveInput::Disabled;
    bReplicates = false;
}

bool ACityLiveEvidenceActor::Configure(const FString& InRole, const FString& InDomain, const FString& RecordRaw, int32 InGeneration)
{
    if (!Role.IsEmpty() || (!CityLCER::Exact(InRole, TEXT("head_anchor")) && !CityLCER::Exact(InRole, TEXT("resource_state"))) ||
        (!CityLCER::Exact(InDomain, TEXT("domain_A")) && !CityLCER::Exact(InDomain, TEXT("domain_B"))) || (InGeneration != 0 && InGeneration != 1))
        return false;
    TSharedPtr<FJsonObject> Record(nullptr);
    if (!CityLCER::Parse(RecordRaw, Record)) return false;
    const FString ExpectedHash = InGeneration == 0
        ? TEXT("8cea1aa6ae3ab2d7a25b6b660c91c26d26a1340ab4f2b67e134f7b7feb12cb12")
        : TEXT("8e2862666a75833c8cff5c1faf9b783fb1d694de9df94fb5a4663fef599ea63c");
    const FString ReceivedHash = CityLCER::Digest(RecordRaw);
    if (!CityLCER::Exact(ReceivedHash, ExpectedHash)) return false;
    Role = InRole; Domain = InDomain; RawSha256 = ReceivedHash;
    Generation = InGeneration; AcceptedRecordRaw = RecordRaw;
    if (CityLCER::Exact(Role, TEXT("resource_state")) && Generation == 1)
        AllocationOwner = Record->GetObjectField(TEXT("current_causal_state"))->GetObjectField(TEXT("shared_slot"))->GetStringField(TEXT("allocation_owner"));
    return true;
}

void ACityLiveEvidenceResource::DisableProposals()
{
    bProposalCapability = false;
}

bool ACityLiveEvidenceResource::Interact(const TSharedPtr<FJsonObject>& Routing, TSharedPtr<FJsonObject>& Result)
{
    if (!IsInGameThread() || !bProposalCapability || InteractionCounter != 0 || Generation != 0 ||
        !CityLCER::Exact(Role, TEXT("resource_state")) || !AllocationOwner.IsEmpty() || !GetWorld() ||
        !CityLCER::Keys(Routing, {TEXT("witness_id"), TEXT("domain"), TEXT("launch_id"), TEXT("operation_id"), TEXT("binding_sha256")}) ||
        !CityLCER::Exact(Routing->GetStringField(TEXT("domain")), Domain) || !CityLCER::Exact(Routing->GetStringField(TEXT("operation_id")), TEXT("emit_0001")))
        return false;
    TSharedPtr<FJsonObject> Record(nullptr);
    if (!CityLCER::Parse(AcceptedRecordRaw, Record) || !CityLCER::Exact(CityLCER::Digest(AcceptedRecordRaw), RawSha256)) return false;
    const auto Contract = Record->GetObjectField(TEXT("current_causal_state"))->GetObjectField(TEXT("external_consequence_contracts"))->GetObjectField(Domain);
    // This single physical Actor interaction consumes its proposal capability.
    ++InteractionCounter;
    bProposalCapability = false;
    const FString CanonicalHash = CityLCER::Digest(AcceptedRecordRaw.LeftChop(1));
    const FString PhysicalActor = Contract->GetStringField(TEXT("physical_actor_id"));
    const FString InputId = Contract->GetStringField(TEXT("permitted_input_id"));
    const FString PhysicalEventId = Contract->GetStringField(TEXT("permitted_physical_event_id"));
    const FString Outcome = Contract->GetStringField(TEXT("observed_outcome"));
    const auto Q = MakeShared<FJsonObject>();
    const auto Evidence = MakeShared<FJsonObject>();
    Evidence->SetStringField(TEXT("outcome_state"), Outcome);
    Evidence->SetStringField(TEXT("physical_actor_id"), PhysicalActor);
    Q->SetObjectField(TEXT("evidence"), Evidence);
    Q->SetStringField(TEXT("input_id"), InputId);
    const auto Observed = MakeShared<FJsonObject>();
    Observed->SetStringField(TEXT("state"), Outcome);
    Q->SetObjectField(TEXT("observed_outcome"), Observed);
    Q->SetStringField(TEXT("occurrence_time"), TEXT("t0/30"));
    Q->SetStringField(TEXT("physical_event_id"), PhysicalEventId);
    const auto Effect = MakeShared<FJsonObject>();
    Effect->SetStringField(TEXT("op"), TEXT("replace"));
    Effect->SetStringField(TEXT("path"), TEXT("/current_causal_state/shared_slot/allocation_owner"));
    Effect->SetStringField(TEXT("value"), Contract->GetStringField(TEXT("permitted_owner")));
    Q->SetObjectField(TEXT("proposed_effect"), Effect);
    Q->SetStringField(TEXT("protocol_version"), TEXT("ConcurrentExternalEvidence.v1"));
    const auto Source = MakeShared<FJsonObject>();
    Source->SetStringField(TEXT("domain"), Domain);
    Source->SetStringField(TEXT("source_payload_raw_sha256"), RawSha256);
    Source->SetStringField(TEXT("source_record_hash"), CanonicalHash);
    Source->SetStringField(TEXT("system"), TEXT("crew_physical_simulation"));
    Q->SetObjectField(TEXT("source"), Source);
    Q->SetObjectField(TEXT("target"), Contract->GetObjectField(TEXT("target")));
    Evidence->SetStringField(TEXT("evidence_digest"), CityLCER::Digest(CityLCER::Canonical(MakeShared<FJsonValueObject>(Q))));
    const FString QRaw = CityLCER::Stored(Q);
    const FString QRawHash = CityLCER::Digest(QRaw);
    const FString QCanonicalHash = CityLCER::Digest(QRaw.LeftChop(1));
    const auto Acceptance = MakeShared<FJsonObject>();
    Acceptance->SetStringField(TEXT("receipt_schema"), TEXT("ConcurrentMaterializationAcceptanceReceipt.v1"));
    Acceptance->SetStringField(TEXT("process_instance_id"), Routing->GetStringField(TEXT("launch_id")));
    Acceptance->SetStringField(TEXT("materialization_domain"), Domain);
    Acceptance->SetStringField(TEXT("accepted_canonical_hash"), CanonicalHash);
    Acceptance->SetStringField(TEXT("accepted_raw_payload_sha256"), RawSha256);
    Acceptance->SetStringField(TEXT("materialized_physical_actor_id"), PhysicalActor);
    Acceptance->SetField(TEXT("materialized_shared_slot_owner"), MakeShared<FJsonValueNull>());
    Acceptance->SetBoolField(TEXT("proposal_capability_enabled"), true);
    const auto Receipt = MakeShared<FJsonObject>();
    Receipt->SetStringField(TEXT("receipt_schema"), TEXT("ConcurrentEvidenceEmissionReceipt.v1"));
    Receipt->SetStringField(TEXT("process_instance_id"), Routing->GetStringField(TEXT("launch_id")));
    Receipt->SetStringField(TEXT("materialization_domain"), Domain);
    Receipt->SetStringField(TEXT("accepted_canonical_hash"), CanonicalHash);
    Receipt->SetStringField(TEXT("accepted_raw_payload_sha256"), RawSha256);
    Receipt->SetStringField(TEXT("materialized_physical_actor_id"), PhysicalActor);
    Receipt->SetStringField(TEXT("emitted_input_id"), InputId);
    Receipt->SetStringField(TEXT("emitted_physical_event_id"), PhysicalEventId);
    Receipt->SetStringField(TEXT("emitted_q_canonical_hash"), QCanonicalHash);
    Receipt->SetStringField(TEXT("emitted_q_raw_sha256"), QRawHash);
    const auto Wrapper = MakeShared<FJsonObject>();
    Wrapper->Values = Routing->Values;
    Wrapper->SetStringField(TEXT("schema"), TEXT("city.live_evidence_emission.v1"));
    Wrapper->SetStringField(TEXT("q_raw_sha256"), QRawHash);
    Wrapper->SetStringField(TEXT("q_canonical_hash"), QCanonicalHash);
    Wrapper->SetStringField(TEXT("physical_event_id"), PhysicalEventId);
    Wrapper->SetStringField(TEXT("source_record_hash"), CanonicalHash);
    Wrapper->SetNumberField(TEXT("interaction_counter"), InteractionCounter);
    const auto Physical = MakeShared<FJsonObject>();
    Physical->Values = Routing->Values;
    Physical->SetStringField(TEXT("schema"), TEXT("city.live_evidence_physical_event.v1"));
    Physical->SetStringField(TEXT("actor_id"), GetWorld()->GetPathName() + TEXT("|") + GetPathName());
    Physical->SetStringField(TEXT("physical_event_id"), PhysicalEventId);
    Physical->SetNumberField(TEXT("interaction_counter"), InteractionCounter);
    Physical->SetStringField(TEXT("accepted_record_raw_sha256"), RawSha256);
    Physical->SetStringField(TEXT("q_raw_sha256"), QRawHash);
    Physical->SetStringField(TEXT("q_canonical_hash"), QCanonicalHash);
    Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("q_raw_utf8"), QRaw);
    Result->SetStringField(TEXT("acceptance_receipt_raw_utf8"), CityLCER::Stored(Acceptance));
    Result->SetStringField(TEXT("emission_receipt_raw_utf8"), CityLCER::Stored(Receipt));
    Result->SetObjectField(TEXT("wrapper"), Wrapper);
    Result->SetObjectField(TEXT("physical_event"), Physical);
    return true;
}
