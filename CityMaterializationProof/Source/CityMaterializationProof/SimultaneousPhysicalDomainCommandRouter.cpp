#include "SimultaneousPhysicalDomainCommandRouter.h"

#include "SimultaneousPhysicalDomainProofAdapter.h"
#include "SimultaneousPhysicalRebindProbe.h"
#include "CityMaterializationProof.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "Misc/App.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#include <openssl/sha.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

namespace
{
constexpr TCHAR Scenario[] = TEXT("simultaneous-physical-domains-v1");
constexpr TCHAR BindingSchema[] = TEXT("SimultaneousPhysicalDomainProcessBinding.v1");
constexpr TCHAR BindCommandSchema[] = TEXT("SimultaneousPhysicalDomainBindInvocation.v1");
constexpr TCHAR RefreshCommandSchema[] = TEXT("SimultaneousPhysicalDomainRefreshInvocation.v1");
constexpr TCHAR InspectionCommandSchema[] = TEXT("SimultaneousPhysicalDomainInspectionInvocation.v1");

FString SPDEscapeJsonString(const FString& Value)
{
    FString Result(TEXT("\""));
    for (TCHAR Character : Value)
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
            if (Character < 0x20 || Character > 0x7f)
            {
                Result += FString::Printf(TEXT("\\u%04x"), static_cast<uint32>(Character));
            }
            else
            {
                Result.AppendChar(Character);
            }
        }
    }
    Result += TEXT("\"");
    return Result;
}

bool DuplicateMemberScan(const FString& Canonical)
{
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Canonical);
    TArray<TSet<FString>> ObjectKeys;
    EJsonNotation Notation;
    while (Reader->ReadNext(Notation))
    {
        const FString Identifier = Reader->GetIdentifier();
        if (!Identifier.IsEmpty() && ObjectKeys.Num() > 0)
        {
            if (ObjectKeys.Last().Contains(Identifier))
            {
                return true;
            }
            ObjectKeys.Last().Add(Identifier);
        }
        if (Notation == EJsonNotation::ObjectStart)
        {
            ObjectKeys.AddDefaulted();
        }
        else if (Notation == EJsonNotation::ObjectEnd)
        {
            if (ObjectKeys.Num() == 0)
            {
                return true;
            }
            ObjectKeys.Pop();
        }
    }
    return ObjectKeys.Num() != 0 || !Reader->GetErrorMessage().IsEmpty();
}

bool DescriptorIsPipe(int Descriptor)
{
    struct stat Info {};
    return fstat(Descriptor, &Info) == 0 && S_ISFIFO(Info.st_mode);
}
}

namespace SimultaneousPhysicalDomainJson
{
FString CanonicalizeValue(const TSharedPtr<FJsonValue>& Value)
{
    if (!Value.IsValid())
    {
        return TEXT("null");
    }
    switch (Value->Type)
    {
    case EJson::None:
    case EJson::Null:
        return TEXT("null");
    case EJson::String:
        return SPDEscapeJsonString(Value->AsString());
    case EJson::Number:
    {
        const double Number = Value->AsNumber();
        if (!FMath::IsFinite(Number))
        {
            return TEXT("null");
        }
        const double Integral = FMath::RoundToDouble(Number);
        if (Number == Integral && FMath::Abs(Number) <= 9007199254740991.0)
        {
            return FString::Printf(TEXT("%.0f"), Number);
        }
        FString Result = FString::Printf(TEXT("%.17g"), Number);
        Result.ReplaceInline(TEXT("E"), TEXT("e"));
        Result.ReplaceInline(TEXT("e+"), TEXT("e"));
        return Result;
    }
    case EJson::Boolean:
        return Value->AsBool() ? TEXT("true") : TEXT("false");
    case EJson::Array:
    {
        TArray<FString> Members;
        for (const TSharedPtr<FJsonValue>& Member : Value->AsArray())
        {
            Members.Add(CanonicalizeValue(Member));
        }
        return FString::Printf(TEXT("[%s]"), *FString::Join(Members, TEXT(",")));
    }
    case EJson::Object:
        return CanonicalizeObject(Value->AsObject());
    }
    return TEXT("null");
}

FString CanonicalizeObject(const TSharedPtr<FJsonObject>& Object)
{
    if (!Object.IsValid())
    {
        return TEXT("null");
    }
    TArray<TPair<FString, TSharedPtr<FJsonValue>>> SortedValues;
    for (const auto& Pair : Object->Values)
    {
        SortedValues.Emplace(FString(Pair.Key), Pair.Value);
    }
    SortedValues.Sort([](const auto& A, const auto& B) { return A.Key < B.Key; });
    TArray<FString> Members;
    for (const auto& Pair : SortedValues)
    {
        Members.Add(SPDEscapeJsonString(Pair.Key) + TEXT(":") + CanonicalizeValue(Pair.Value));
    }
    return FString::Printf(TEXT("{%s}"), *FString::Join(Members, TEXT(",")));
}

bool ParseCanonicalObject(const FString& Canonical, TSharedPtr<FJsonObject>& OutObject)
{
    if (Canonical.IsEmpty() || Canonical.Contains(TEXT("\r")) || Canonical.Contains(TEXT("\n")) || DuplicateMemberScan(Canonical))
    {
        return false;
    }
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Canonical);
    if (!FJsonSerializer::Deserialize(Reader, OutObject) || !OutObject.IsValid())
    {
        return false;
    }
    return CanonicalizeObject(OutObject) == Canonical;
}

FString Sha256Bytes(const TArray<uint8>& Bytes)
{
    uint8 Digest[SHA256_DIGEST_LENGTH];
    SHA256(Bytes.GetData(), Bytes.Num(), Digest);
    FString Result;
    for (uint8 Byte : Digest)
    {
        Result += FString::Printf(TEXT("%02x"), Byte);
    }
    return Result;
}

FString Sha256Utf8(const FString& Value)
{
    FTCHARToUTF8 Utf8(*Value);
    TArray<uint8> Bytes;
    Bytes.Append(reinterpret_cast<const uint8*>(Utf8.Get()), Utf8.Length());
    return Sha256Bytes(Bytes);
}

bool LoadExactStoredJsonNoFollow(const FString& Path, TArray<uint8>& OutBytes, TSharedPtr<FJsonObject>& OutObject)
{
    FTCHARToUTF8 PathUtf8(*Path);
    const int Descriptor = open(PathUtf8.Get(), O_RDONLY | O_NOFOLLOW);
    if (Descriptor < 0)
    {
        return false;
    }
    struct stat Info {};
    if (fstat(Descriptor, &Info) != 0 || !S_ISREG(Info.st_mode) || Info.st_nlink != 1 || Info.st_size < 3 || Info.st_size > 16 * 1024 * 1024)
    {
        close(Descriptor);
        return false;
    }
    OutBytes.SetNumUninitialized(static_cast<int32>(Info.st_size));
    ssize_t Total = 0;
    while (Total < Info.st_size)
    {
        const ssize_t Read = ::read(Descriptor, OutBytes.GetData() + Total, static_cast<size_t>(Info.st_size - Total));
        if (Read <= 0)
        {
            close(Descriptor);
            return false;
        }
        Total += Read;
    }
    close(Descriptor);
    if (OutBytes.Last() != '\n')
    {
        return false;
    }
    int32 Newlines = 0;
    for (uint8 Byte : OutBytes)
    {
        if (Byte == '\r') return false;
        if (Byte == '\n') ++Newlines;
    }
    if (Newlines != 1)
    {
        return false;
    }
    FUTF8ToTCHAR Converted(reinterpret_cast<const ANSICHAR*>(OutBytes.GetData()), OutBytes.Num() - 1);
    const FString Canonical(Converted.Length(), Converted.Get());
    return ParseCanonicalObject(Canonical, OutObject);
}

bool HasExactKeys(const TSharedPtr<FJsonObject>& Object, std::initializer_list<const TCHAR*> Keys)
{
    if (!Object.IsValid() || Object->Values.Num() != static_cast<int32>(Keys.size()))
    {
        return false;
    }
    for (const TCHAR* Key : Keys)
    {
        if (!Object->HasField(Key)) return false;
    }
    return true;
}

bool ExactString(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, const TCHAR* Expected)
{
    FString Value;
    return Object.IsValid() && Object->TryGetStringField(Field, Value) && Value == Expected;
}

bool IsLowerSha256(const FString& Value)
{
    if (Value.Len() != 64) return false;
    for (TCHAR Character : Value)
    {
        if (!((Character >= '0' && Character <= '9') || (Character >= 'a' && Character <= 'f'))) return false;
    }
    return true;
}

void EmitStructuredObject(const TSharedPtr<FJsonObject>& Object)
{
    const FString Canonical = CanonicalizeObject(Object);
    FTCHARToUTF8 Utf8(*Canonical);
    fwrite(Utf8.Get(), 1, Utf8.Length(), stdout);
    fwrite("\n", 1, 1, stdout);
    fflush(stdout);
}
}

class FSPDInputRunnable final : public FRunnable
{
public:
    explicit FSPDInputRunnable(TQueue<FString, EQueueMode::Mpsc>& InQueue) : Queue(InQueue) {}

    virtual uint32 Run() override
    {
        TArray<uint8> Buffer;
        while (!bStop)
        {
            uint8 Byte = 0;
            const ssize_t Count = ::read(STDIN_FILENO, &Byte, 1);
            if (Count <= 0)
            {
                break;
            }
            if (Byte == '\n')
            {
                FUTF8ToTCHAR Converted(reinterpret_cast<const ANSICHAR*>(Buffer.GetData()), Buffer.Num());
                Queue.Enqueue(FString(Converted.Length(), Converted.Get()));
                Buffer.Reset();
            }
            else if (Byte == '\r' || Buffer.Num() >= 4 * 1024 * 1024)
            {
                Queue.Enqueue(TEXT("<invalid-line>"));
                Buffer.Reset();
            }
            else
            {
                Buffer.Add(Byte);
            }
        }
        return 0;
    }

    virtual void Stop() override { bStop = true; }

private:
    TQueue<FString, EQueueMode::Mpsc>& Queue;
    FThreadSafeBool bStop = false;
};

ASimultaneousPhysicalDomainCommandRouter::ASimultaneousPhysicalDomainCommandRouter()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.01f;
}

void ASimultaneousPhysicalDomainCommandRouter::BeginPlay()
{
    Super::BeginPlay();
    InputRunnable = new FSPDInputRunnable(PendingLines);
    InputThread = FRunnableThread::Create(InputRunnable, TEXT("SimultaneousPhysicalDomainStdin"));
    if (InputThread == nullptr)
    {
        bProtocolFailed = true;
        EmitFailure(TEXT("invocation_read"), TEXT("stdin_thread_creation_failed"));
    }
}

void ASimultaneousPhysicalDomainCommandRouter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    FString Line;
    while (PendingLines.Dequeue(Line))
    {
        HandleLine(Line);
    }
}

void ASimultaneousPhysicalDomainCommandRouter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (InputRunnable != nullptr)
    {
        InputRunnable->Stop();
    }
    // The process owns the blocking stdin endpoint.  Do not replace or reopen
    // it to join the proof-local reader; process termination closes it.
    Super::EndPlay(EndPlayReason);
}

bool ASimultaneousPhysicalDomainCommandRouter::VerifyObservableBinding(const TSharedPtr<FJsonObject>& Binding, FString& OutReason) const
{
    using namespace SimultaneousPhysicalDomainJson;
    if (!HasExactKeys(Binding, {
        TEXT("binding_schema"), TEXT("proof_scenario"), TEXT("witness_id"), TEXT("domain_role"), TEXT("harness_launch_id"),
        TEXT("pid"), TEXT("macos_process_start"), TEXT("executable_realpath"), TEXT("executable_raw_sha256"),
        TEXT("unreal_engine_build_identity"), TEXT("entry_map_package_identity"), TEXT("project_realpath"),
        TEXT("project_raw_sha256"), TEXT("project_config_and_module_inventory_raw_sha256"), TEXT("process_root_realpath"),
        TEXT("launch_argv_raw_sha256"), TEXT("launch_environment_audit_raw_sha256"), TEXT("launch_cwd_realpath"),
        TEXT("inherited_descriptor_map_raw_sha256"), TEXT("control_pipe_id"), TEXT("structured_output_pipe_id"),
        TEXT("diagnostic_pipe_id")
    }) || !ExactString(Binding, TEXT("binding_schema"), BindingSchema) ||
        !ExactString(Binding, TEXT("proof_scenario"), Scenario))
    {
        OutReason = TEXT("binding_structure_mismatch");
        return false;
    }
    FString DomainRole;
    FString WitnessId;
    FString HarnessLaunchId;
    FString ProcessRoot;
    double PidNumber = 0;
    if (!Binding->TryGetStringField(TEXT("domain_role"), DomainRole) ||
        (DomainRole != TEXT("domain_A") && DomainRole != TEXT("domain_B")) ||
        !Binding->TryGetStringField(TEXT("witness_id"), WitnessId) || WitnessId.IsEmpty() ||
        !Binding->TryGetStringField(TEXT("harness_launch_id"), HarnessLaunchId) ||
        HarnessLaunchId != WitnessId + TEXT("/") + DomainRole + TEXT("/launch_0001") ||
        !Binding->TryGetStringField(TEXT("process_root_realpath"), ProcessRoot) || ProcessRoot.IsEmpty() ||
        !Binding->TryGetNumberField(TEXT("pid"), PidNumber) || static_cast<int32>(PidNumber) != FPlatformProcess::GetCurrentProcessId())
    {
        OutReason = TEXT("binding_observable_identity_mismatch");
        return false;
    }
    for (const TCHAR* Field : {
        TEXT("executable_raw_sha256"), TEXT("project_raw_sha256"), TEXT("project_config_and_module_inventory_raw_sha256"),
        TEXT("launch_argv_raw_sha256"), TEXT("launch_environment_audit_raw_sha256"), TEXT("inherited_descriptor_map_raw_sha256")
    })
    {
        FString Digest;
        if (!Binding->TryGetStringField(Field, Digest) || !IsLowerSha256(Digest))
        {
            OutReason = TEXT("binding_digest_invalid");
            return false;
        }
    }
    // Unreal changes the process cwd to its engine base before GameMode
    // BeginPlay.  The launch-time cwd is therefore verified against the exact
    // repository parent derived from the already bound project path; the
    // harness separately proves the posix_spawn chdir action.  The later
    // engine cwd is platform context and never selects Phase-3 semantics.
    FString ExpectedCwd = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::GetPath(FPaths::GetProjectFilePath()), TEXT("..")));
    FString BindingCwd;
    if (!Binding->TryGetStringField(TEXT("launch_cwd_realpath"), BindingCwd))
    {
        OutReason = TEXT("binding_cwd_missing");
        return false;
    }
    BindingCwd = FPaths::ConvertRelativePathToFull(BindingCwd);
    FPaths::NormalizeDirectoryName(ExpectedCwd);
    FPaths::NormalizeDirectoryName(BindingCwd);
    if (BindingCwd != ExpectedCwd)
    {
        OutReason = TEXT("binding_cwd_mismatch");
        return false;
    }
    if (!DescriptorIsPipe(STDIN_FILENO) || !DescriptorIsPipe(STDOUT_FILENO) || !DescriptorIsPipe(STDERR_FILENO))
    {
        OutReason = TEXT("binding_original_descriptor_pipe_mismatch");
        return false;
    }
    return true;
}

bool ASimultaneousPhysicalDomainCommandRouter::AcceptBinding(const TSharedPtr<FJsonObject>& Command, FString& OutReason)
{
    using namespace SimultaneousPhysicalDomainJson;
    if (bBindingAccepted || !HasExactKeys(Command, {
        TEXT("command_schema"), TEXT("proof_scenario"), TEXT("operation"),
        TEXT("operational_process_instance_id"), TEXT("process_binding")
    }) || !ExactString(Command, TEXT("command_schema"), BindCommandSchema) ||
        !ExactString(Command, TEXT("proof_scenario"), Scenario) ||
        !ExactString(Command, TEXT("operation"), TEXT("bind_process_once")))
    {
        OutReason = TEXT("invalid_or_duplicate_binding_command");
        return false;
    }
    const TSharedPtr<FJsonObject>* Binding = nullptr;
    FString InstanceId;
    if (!Command->TryGetObjectField(TEXT("process_binding"), Binding) || !Binding ||
        !Command->TryGetStringField(TEXT("operational_process_instance_id"), InstanceId) || !IsLowerSha256(InstanceId) ||
        Sha256Utf8(CanonicalizeObject(*Binding)) != InstanceId || !VerifyObservableBinding(*Binding, OutReason))
    {
        if (OutReason.IsEmpty()) OutReason = TEXT("process_binding_digest_mismatch");
        return false;
    }
    ImmutableBinding.CompleteBinding = *Binding;
    ImmutableBinding.OperationalProcessInstanceId = InstanceId;
    ImmutableBinding.ProcessBindingRawSha256 = Sha256Utf8(CanonicalizeObject(*Binding) + TEXT("\n"));
    (*Binding)->TryGetStringField(TEXT("domain_role"), ImmutableBinding.DomainRole);
    (*Binding)->TryGetStringField(TEXT("witness_id"), ImmutableBinding.WitnessId);
    (*Binding)->TryGetStringField(TEXT("process_root_realpath"), ImmutableBinding.ProcessRootRealpath);
    double PidNumber = 0;
    (*Binding)->TryGetNumberField(TEXT("pid"), PidNumber);
    ImmutableBinding.Pid = static_cast<int32>(PidNumber);

    Adapter = GetWorld()->SpawnActor<ASimultaneousPhysicalDomainProofAdapter>();
    Probe = GetWorld()->SpawnActor<ASimultaneousPhysicalRebindProbe>();
    if (Adapter == nullptr || Probe == nullptr || !Probe->BindProcessIdentity(ImmutableBinding))
    {
        OutReason = TEXT("phase3_actor_spawn_or_binding_failed");
        return false;
    }
    TSharedPtr<FJsonObject> LaunchReceipt;
    if (!Adapter->MaterializeLaunch(ImmutableBinding, LaunchReceipt, OutReason))
    {
        return false;
    }
    bBindingAccepted = true;
    EmitStructuredObject(LaunchReceipt);
    return true;
}

void ASimultaneousPhysicalDomainCommandRouter::HandleLine(const FString& CanonicalLine)
{
    using namespace SimultaneousPhysicalDomainJson;
    if (bProtocolFailed)
    {
        EmitFailure(TEXT("invocation_read"), TEXT("command_after_protocol_failure"));
        return;
    }
    TSharedPtr<FJsonObject> Command;
    if (!ParseCanonicalObject(CanonicalLine, Command))
    {
        bProtocolFailed = true;
        EmitFailure(TEXT("invocation_read"), TEXT("noncanonical_command"));
        return;
    }
    if (!bBindingAccepted)
    {
        FString Reason;
        if (!AcceptBinding(Command, Reason))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("process_binding_identity_verification"), Reason);
        }
        return;
    }

    FString Schema;
    Command->TryGetStringField(TEXT("command_schema"), Schema);
    FString Reason;
    TSharedPtr<FJsonObject> Result;
    if (Schema == InspectionCommandSchema)
    {
        if (!HasExactKeys(Command, {TEXT("command_schema"), TEXT("proof_scenario"), TEXT("domain_role"), TEXT("operation"), TEXT("inspection_id")}) ||
            !ExactString(Command, TEXT("proof_scenario"), Scenario) ||
            !ExactString(Command, TEXT("domain_role"), *ImmutableBinding.DomainRole) ||
            !ExactString(Command, TEXT("operation"), TEXT("inspect_published_route_once")))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("inspection_invocation_read"), TEXT("invalid_inspection_command"));
            return;
        }
        FString InspectionId;
        Command->TryGetStringField(TEXT("inspection_id"), InspectionId);
        const bool bExpectedLaunchSlot = !bLaunchInspectionAccepted && !bRefreshAccepted && InspectionId == TEXT("launch_physical_0001");
        const bool bExpectedRefreshSlot = bLaunchInspectionAccepted && bRefreshAccepted && !bRefreshInspectionAccepted && InspectionId == TEXT("refresh_physical_0001");
        if ((!bExpectedLaunchSlot && !bExpectedRefreshSlot) || !Probe->InspectPublishedRoute(InspectionId, Result, Reason))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("inspection_invocation_read"), Reason.IsEmpty() ? TEXT("inspection_order_or_probe_failure") : Reason);
            return;
        }
        bLaunchInspectionAccepted |= bExpectedLaunchSlot;
        bRefreshInspectionAccepted |= bExpectedRefreshSlot;
        EmitStructuredObject(Result);
        return;
    }
    if (Schema == RefreshCommandSchema)
    {
        if (!bLaunchInspectionAccepted || bRefreshAccepted || !HasExactKeys(Command, {
            TEXT("command_schema"), TEXT("proof_scenario"), TEXT("domain_role"), TEXT("operation"), TEXT("refresh_id"), TEXT("target_canonical_hash")
        }) || !ExactString(Command, TEXT("proof_scenario"), Scenario) ||
            !ExactString(Command, TEXT("domain_role"), *ImmutableBinding.DomainRole) ||
            !ExactString(Command, TEXT("operation"), TEXT("refresh_once")) ||
            !ExactString(Command, TEXT("refresh_id"), TEXT("h0_to_h1_refresh_0001")) ||
            !ExactString(Command, TEXT("target_canonical_hash"), TEXT("78cc5ffe0c4758c296d8fee0bc2a95e230be0bec0a4aab680806eb670500804a")))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("invocation_read"), TEXT("invalid_duplicate_or_out_of_order_refresh"));
            return;
        }
        if (!Adapter->RefreshOnce(ImmutableBinding, Result, Reason))
        {
            // A prepublication refresh rejection is not a router protocol
            // failure.  The original process remains available for harness
            // diagnostics and termination, but this proof accepts no retry.
            bRefreshAccepted = true;
            EmitFailure(TEXT("refresh_rejected_before_publication"), Reason);
            return;
        }
        bRefreshAccepted = true;
        EmitStructuredObject(Result);
        return;
    }
    bProtocolFailed = true;
    EmitFailure(TEXT("invocation_read"), TEXT("unknown_command_schema"));
}

void ASimultaneousPhysicalDomainCommandRouter::EmitFailure(const FString& PublicationStage, const FString& ReasonCode) const
{
    using namespace SimultaneousPhysicalDomainJson;
    TSharedPtr<FJsonObject> Failure = MakeShared<FJsonObject>();
    Failure->SetStringField(TEXT("diagnostic_schema"), TEXT("SimultaneousPhysicalDomainFailure.v1"));
    Failure->SetStringField(TEXT("proof_scenario"), Scenario);
    Failure->SetStringField(TEXT("domain_role"), ImmutableBinding.DomainRole.IsEmpty() ? TEXT("unbound") : ImmutableBinding.DomainRole);
    Failure->SetStringField(TEXT("operational_process_instance_id"), ImmutableBinding.OperationalProcessInstanceId);
    Failure->SetStringField(TEXT("process_binding_raw_sha256"), ImmutableBinding.ProcessBindingRawSha256);
    Failure->SetStringField(TEXT("represented_hash_if_known"), Adapter != nullptr ? Adapter->GetRepresentedCanonicalHash() : TEXT(""));
    Failure->SetStringField(TEXT("local_publication_stage"), PublicationStage);
    Failure->SetStringField(TEXT("reason_code"), ReasonCode.IsEmpty() ? TEXT("unspecified_local_failure") : ReasonCode);
    EmitStructuredObject(Failure);
}
