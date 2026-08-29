#include "SimultaneousPhysicalDomainCommandRouter.h"

#include "SimultaneousPhysicalDomainProofAdapter.h"
#include "SimultaneousPhysicalRebindProbe.h"
#include "CityMaterializationProof.h"
#include "Dom/JsonObject.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "Misc/App.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#include <openssl/sha.h>
#include <crt_externs.h>
#include <fcntl.h>
#include <libproc.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#include <stdlib.h>
#include <sys/proc_info.h>
#include <sys/stat.h>
#include <unistd.h>

namespace
{
constexpr TCHAR Scenario[] = TEXT("simultaneous-physical-domains-v1.1");
constexpr TCHAR BindingSchema[] = TEXT("SimultaneousPhysicalDomainProcessBinding.v1");
constexpr TCHAR BindCommandSchema[] = TEXT("SimultaneousPhysicalDomainBindInvocation.v1");
constexpr TCHAR RefreshCommandSchema[] = TEXT("SimultaneousPhysicalDomainRefreshInvocation.v1");
constexpr TCHAR InspectionCommandSchema[] = TEXT("SimultaneousPhysicalDomainInspectionInvocation.v1");
constexpr TCHAR LocalStepCommandSchema[] = TEXT("SimultaneousPhysicalDomainLocalStepInvocation.v1");
constexpr TCHAR FaultArmCommandSchema[] = TEXT("SimultaneousPhysicalDomainFaultArmInvocation.v1");

bool IsAllowedWitnessId(const FString& Value)
{
    return Value == TEXT("w1_a_then_b") || Value == TEXT("w2_b_then_a") ||
        Value == TEXT("w3_stale_quarantine") || Value == TEXT("w4_head_observation_failure") ||
        Value == TEXT("w5_retention_baseline") || Value == TEXT("w5_retention_perturbed") ||
        Value == TEXT("w6_asymmetric_a_synchronized") || Value == TEXT("w6_asymmetric_b_synchronized") ||
        Value == TEXT("w7_destroy_a") || Value == TEXT("w7_destroy_b") ||
        Value == TEXT("w8_guard_open_control") || Value == TEXT("f_refresh_fault") ||
        Value == TEXT("f_physical_observation_fault");
}

bool IsRefreshFaultStage(const FString& Value)
{
    return Value == TEXT("invocation_read") || Value == TEXT("visible_input_inventory") ||
        Value == TEXT("payload_raw_byte_verification") || Value == TEXT("payload_parse_and_canonical_identity_verification") ||
        Value == TEXT("operation_receipt_verification") || Value == TEXT("projection_verification") ||
        Value == TEXT("visible_command_bundle_cross_field_verification") || Value == TEXT("process_binding_identity_verification") ||
        Value == TEXT("retained_local_state_projection_extraction") || Value == TEXT("discard_required_state_poison_check") ||
        Value == TEXT("empty_authoritative_candidate_construction") || Value == TEXT("H1_authoritative_fact_derivation") ||
        Value == TEXT("projection_slot_binding") || Value == TEXT("private_candidate_validation") ||
        Value == TEXT("retained_local_state_attachment") || Value == TEXT("prepublication_cross_field_validation") ||
        Value == TEXT("local_atomic_publication") || Value == TEXT("materialization_receipt_emission");
}

bool IsObservationFaultStage(const FString& Value)
{
    return Value == TEXT("inspection_invocation_read") || Value == TEXT("immutable_process_binding_verification") ||
        Value == TEXT("role_probe_tag_derivation") || Value == TEXT("live_world_actor_enumeration") ||
        Value == TEXT("exact_actor_count_check") || Value == TEXT("live_mesh_component_lookup") ||
        Value == TEXT("live_mesh_visibility_and_material_parameter_read") || Value == TEXT("live_label_component_lookup") ||
        Value == TEXT("live_label_visibility_text_and_color_read") || Value == TEXT("independent_surface_consistency_classification") ||
        Value == TEXT("physical_observation_emission") || Value == TEXT("harness_receipt_observation_head_cross_check");
}

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

bool ResolveRealpath(const FString& Input, FString& OutRealpath)
{
    FTCHARToUTF8 InputUtf8(*Input);
    char Resolved[PATH_MAX] {};
    if (realpath(InputUtf8.Get(), Resolved) == nullptr)
    {
        return false;
    }
    OutRealpath = UTF8_TO_TCHAR(Resolved);
    return FPaths::IsRelative(OutRealpath) == false;
}

bool HashRegularFileRawSha256(const FString& Realpath, FString& OutDigest)
{
    FTCHARToUTF8 PathUtf8(*Realpath);
    const int Descriptor = open(PathUtf8.Get(), O_RDONLY | O_NOFOLLOW);
    if (Descriptor < 0)
    {
        return false;
    }
    struct stat Info {};
    if (fstat(Descriptor, &Info) != 0 || !S_ISREG(Info.st_mode))
    {
        close(Descriptor);
        return false;
    }
    SHA256_CTX Context {};
    SHA256_Init(&Context);
    TArray<uint8> Buffer;
    Buffer.SetNumUninitialized(1024 * 1024);
    bool bSucceeded = true;
    while (true)
    {
        const ssize_t Count = ::read(Descriptor, Buffer.GetData(), Buffer.Num());
        if (Count == 0) break;
        if (Count < 0)
        {
            bSucceeded = false;
            break;
        }
        SHA256_Update(&Context, Buffer.GetData(), static_cast<size_t>(Count));
    }
    close(Descriptor);
    uint8 Digest[SHA256_DIGEST_LENGTH] {};
    if (!bSucceeded)
    {
        return false;
    }
    SHA256_Final(Digest, &Context);
    OutDigest.Reset();
    for (int32 Index = 0; Index < SHA256_DIGEST_LENGTH; ++Index)
    {
        OutDigest += FString::Printf(TEXT("%02x"), Digest[Index]);
    }
    return true;
}

FString UuidString(const uint8* Bytes)
{
    FString Result;
    for (int32 Index = 0; Index < 16; ++Index)
    {
        if (Index == 4 || Index == 6 || Index == 8 || Index == 10) Result += TEXT("-");
        Result += FString::Printf(TEXT("%02x"), Bytes[Index]);
    }
    return Result;
}

bool LoadedMachOUuid(const mach_header* Header, FString& OutUuid)
{
    if (Header == nullptr ||
        (Header->magic != MH_MAGIC && Header->magic != MH_MAGIC_64))
    {
        return false;
    }
    const uint8* Cursor = reinterpret_cast<const uint8*>(Header) +
        (Header->magic == MH_MAGIC_64 ? sizeof(mach_header_64) : sizeof(mach_header));
    for (uint32 Index = 0; Index < Header->ncmds; ++Index)
    {
        const load_command* Command = reinterpret_cast<const load_command*>(Cursor);
        if (Command->cmdsize < sizeof(load_command)) return false;
        if (Command->cmd == LC_UUID && Command->cmdsize >= sizeof(uuid_command))
        {
            const uuid_command* Uuid = reinterpret_cast<const uuid_command*>(Command);
            OutUuid = UuidString(Uuid->uuid);
            return true;
        }
        Cursor += Command->cmdsize;
    }
    return false;
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

namespace
{
FString GRuntimeAuditRole;
FString GRuntimeAuditInstanceId;
FString GRuntimeAuditBindingDigest;
int32 GRuntimeAuditSequence = 0;
bool GRuntimeAuditReady = false;

void EmitRuntimeInputTrace(
    const FString& InputClass,
    const FString& Operation,
    const FString& SourceIdentity,
    const FString& RawSha256,
    const TSharedPtr<FJsonObject>& Metadata)
{
    using namespace SimultaneousPhysicalDomainJson;
    if (!GRuntimeAuditReady || !IsLowerSha256(RawSha256)) return;
    TSharedPtr<FJsonObject> Event = MakeShared<FJsonObject>();
    Event->SetStringField(TEXT("trace_schema"), TEXT("SimultaneousPhysicalDomainRuntimeInputTraceEvent.v1"));
    Event->SetStringField(TEXT("proof_scenario"), Scenario);
    Event->SetStringField(TEXT("domain_role"), GRuntimeAuditRole);
    Event->SetStringField(TEXT("operational_process_instance_id"), GRuntimeAuditInstanceId);
    Event->SetStringField(TEXT("process_binding_raw_sha256"), GRuntimeAuditBindingDigest);
    Event->SetNumberField(TEXT("sequence"), ++GRuntimeAuditSequence);
    Event->SetStringField(TEXT("input_class"), InputClass);
    Event->SetStringField(TEXT("operation"), Operation);
    Event->SetStringField(TEXT("source_identity"), SourceIdentity);
    Event->SetStringField(TEXT("observed_raw_sha256"), RawSha256);
    Event->SetObjectField(TEXT("metadata"), Metadata.IsValid() ? Metadata : MakeShared<FJsonObject>());
    EmitStructuredObject(Event);
}
}

namespace SimultaneousPhysicalDomainRuntimeAudit
{
bool ResolveAndHashRegularFile(const FString& Path, FString& OutRealpath, FString& OutRawSha256)
{
    return ResolveRealpath(Path, OutRealpath) && HashRegularFileRawSha256(OutRealpath, OutRawSha256);
}

void Initialize(
    const FString& DomainRole,
    const FString& OperationalProcessInstanceId,
    const FString& ProcessBindingRawSha256)
{
    GRuntimeAuditRole = DomainRole;
    GRuntimeAuditInstanceId = OperationalProcessInstanceId;
    GRuntimeAuditBindingDigest = ProcessBindingRawSha256;
    GRuntimeAuditSequence = 0;
    GRuntimeAuditReady =
        (DomainRole == TEXT("domain_A") || DomainRole == TEXT("domain_B")) &&
        SimultaneousPhysicalDomainJson::IsLowerSha256(OperationalProcessInstanceId) &&
        SimultaneousPhysicalDomainJson::IsLowerSha256(ProcessBindingRawSha256);
}

void RecordStdinCommand(const TSharedPtr<FJsonObject>& Command)
{
    using namespace SimultaneousPhysicalDomainJson;
    FString Schema;
    if (!Command.IsValid() || !Command->TryGetStringField(TEXT("command_schema"), Schema)) return;
    const FString Canonical = CanonicalizeObject(Command);
    TSharedPtr<FJsonObject> Metadata = MakeShared<FJsonObject>();
    Metadata->SetStringField(TEXT("command_schema"), Schema);
    Metadata->SetStringField(TEXT("descriptor"), TEXT("fd_0_original_control_pipe_read_endpoint"));
    EmitRuntimeInputTrace(TEXT("stdin_command"), TEXT("canonical_line_read"), TEXT("fd:0"), Sha256Utf8(Canonical + TEXT("\n")), Metadata);
}

void RecordDirectoryInventory(const FString& DirectoryRealpath, const TArray<FString>& SortedMemberNames)
{
    TArray<TSharedPtr<FJsonValue>> Values;
    for (const FString& Name : SortedMemberNames) Values.Add(MakeShared<FJsonValueString>(Name));
    const TSharedPtr<FJsonValue> ArrayValue = MakeShared<FJsonValueArray>(Values);
    TSharedPtr<FJsonObject> Metadata = MakeShared<FJsonObject>();
    Metadata->SetArrayField(TEXT("sorted_member_names"), Values);
    EmitRuntimeInputTrace(
        TEXT("bundle_directory"), TEXT("exact_member_inventory"), DirectoryRealpath,
        SimultaneousPhysicalDomainJson::Sha256Utf8(SimultaneousPhysicalDomainJson::CanonicalizeValue(ArrayValue)), Metadata);
}

void RecordBundleFileRead(
    const FString& FileRealpath,
    const FString& RawSha256,
    int64 Size,
    uint64 Device,
    uint64 Inode)
{
    TSharedPtr<FJsonObject> Metadata = MakeShared<FJsonObject>();
    Metadata->SetStringField(TEXT("device"), FString::Printf(TEXT("%llu"), Device));
    Metadata->SetStringField(TEXT("inode"), FString::Printf(TEXT("%llu"), Inode));
    Metadata->SetNumberField(TEXT("size"), static_cast<double>(Size));
    Metadata->SetStringField(TEXT("descriptor_access"), TEXT("read_only_no_follow"));
    EmitRuntimeInputTrace(TEXT("bundle_file"), TEXT("opened_descriptor_raw_read"), FileRealpath, RawSha256, Metadata);
}

void RecordEngineAssetRead(
    const FString& PackageIdentity,
    const FString& FileRealpath,
    const FString& RawSha256)
{
    TSharedPtr<FJsonObject> Metadata = MakeShared<FJsonObject>();
    Metadata->SetStringField(TEXT("package_identity"), PackageIdentity);
    EmitRuntimeInputTrace(TEXT("engine_asset_package"), TEXT("LoadObject_dependency"), FileRealpath, RawSha256, Metadata);
}

void RecordLiveWorldRead(
    const FString& InspectionId,
    const FString& ReadStage,
    const FString& ObservedValueRawSha256)
{
    TSharedPtr<FJsonObject> Metadata = MakeShared<FJsonObject>();
    Metadata->SetStringField(TEXT("inspection_id"), InspectionId);
    Metadata->SetStringField(TEXT("read_stage"), ReadStage);
    EmitRuntimeInputTrace(TEXT("live_world_state"), TEXT("independent_probe_read"), ReadStage, ObservedValueRawSha256, Metadata);
}
}

namespace
{
bool CaptureOriginalArgv(TArray<FString>& OutArgv)
{
    int* ArgcPointer = _NSGetArgc();
    char*** ArgvPointer = _NSGetArgv();
    if (ArgcPointer == nullptr || ArgvPointer == nullptr || *ArgvPointer == nullptr || *ArgcPointer < 2)
    {
        return false;
    }
    for (int Index = 0; Index < *ArgcPointer; ++Index)
    {
        const char* Raw = (*ArgvPointer)[Index];
        if (Raw == nullptr) return false;
        OutArgv.Add(UTF8_TO_TCHAR(Raw));
    }
    return true;
}

bool BuildRedactedEnvironmentAudit(
    TSharedPtr<FJsonObject>& OutAudit,
    TMap<FString, FString>& OutEnvironment)
{
    char*** EnvironmentPointer = _NSGetEnviron();
    if (EnvironmentPointer == nullptr || *EnvironmentPointer == nullptr) return false;
    for (char** Cursor = *EnvironmentPointer; *Cursor != nullptr; ++Cursor)
    {
        const FString Entry = UTF8_TO_TCHAR(*Cursor);
        FString Key;
        FString Value;
        if (!Entry.Split(TEXT("="), &Key, &Value, ESearchCase::CaseSensitive, ESearchDir::FromStart) ||
            Key.IsEmpty() || OutEnvironment.Contains(Key))
        {
            return false;
        }
        OutEnvironment.Add(Key, Value);
    }
    TArray<FString> Keys;
    OutEnvironment.GetKeys(Keys);
    Keys.Sort([](const FString& A, const FString& B)
    {
        return FCString::Strcmp(*A, *B) < 0;
    });
    TArray<TSharedPtr<FJsonValue>> Entries;
    for (const FString& Key : Keys)
    {
        TSharedPtr<FJsonObject> Item = MakeShared<FJsonObject>();
        Item->SetStringField(TEXT("key"), Key);
        Item->SetStringField(
            TEXT("value_raw_sha256"),
            SimultaneousPhysicalDomainJson::Sha256Utf8(OutEnvironment.FindChecked(Key)));
        Entries.Add(MakeShared<FJsonValueObject>(Item));
    }
    OutAudit = MakeShared<FJsonObject>();
    OutAudit->SetStringField(TEXT("audit_schema"), TEXT("SimultaneousPhysicalDomainLaunchEnvironmentAudit.v1"));
    OutAudit->SetArrayField(TEXT("sorted_entries"), Entries);
    OutAudit->SetBoolField(TEXT("plaintext_values_released"), false);
    OutAudit->SetArrayField(TEXT("proof_semantic_key_allowlist"), {});
    return true;
}

bool CaptureDescriptorState(
    const FString& DomainRole,
    TSharedPtr<FJsonObject>& OutLogicalMap,
    TArray<TSharedPtr<FJsonValue>>& OutKernelIdentities)
{
    OutLogicalMap = MakeShared<FJsonObject>();
    OutLogicalMap->SetStringField(TEXT("descriptor_map_schema"), TEXT("SimultaneousPhysicalDomainInheritedDescriptorMap.v1"));
    const TCHAR* LogicalRoles[] = {
        TEXT("original_control_pipe_read_endpoint"),
        TEXT("original_structured_output_pipe_write_endpoint"),
        TEXT("original_diagnostic_pipe_write_endpoint"),
    };
    const TCHAR* LogicalSuffixes[] = {TEXT("control/0001"), TEXT("stdout/0001"), TEXT("stderr/0001")};
    for (int Descriptor = 0; Descriptor <= 2; ++Descriptor)
    {
        struct stat Info {};
        const int Flags = fcntl(Descriptor, F_GETFL);
        const int ExpectedAccess = Descriptor == STDIN_FILENO ? O_RDONLY : O_WRONLY;
        if (fstat(Descriptor, &Info) != 0 || !S_ISFIFO(Info.st_mode) || Flags < 0 ||
            (Flags & O_ACCMODE) != ExpectedAccess)
        {
            return false;
        }
        TSharedPtr<FJsonObject> Logical = MakeShared<FJsonObject>();
        Logical->SetStringField(TEXT("role"), LogicalRoles[Descriptor]);
        Logical->SetStringField(
            TEXT("pipe_id"), FString::Printf(TEXT("%s/%s"), *DomainRole, LogicalSuffixes[Descriptor]));
        OutLogicalMap->SetObjectField(FString::Printf(TEXT("fd_%d"), Descriptor), Logical);

        TSharedPtr<FJsonObject> Kernel = MakeShared<FJsonObject>();
        Kernel->SetNumberField(TEXT("fd"), Descriptor);
        Kernel->SetStringField(TEXT("file_type"), TEXT("fifo"));
        Kernel->SetStringField(TEXT("access_mode"), Descriptor == STDIN_FILENO ? TEXT("read_only") : TEXT("write_only"));
        Kernel->SetStringField(TEXT("device"), FString::Printf(TEXT("%llu"), static_cast<unsigned long long>(Info.st_dev)));
        Kernel->SetStringField(TEXT("inode"), FString::Printf(TEXT("%llu"), static_cast<unsigned long long>(Info.st_ino)));
        OutKernelIdentities.Add(MakeShared<FJsonValueObject>(Kernel));
    }
    OutLogicalMap->SetStringField(TEXT("all_other_descriptors_at_exec"), TEXT("closed"));
    return true;
}

bool BuildProjectModuleInventory(
    const FString& ProjectRealpath,
    TSharedPtr<FJsonObject>& OutInventory,
    FString& OutInventoryDigest,
    FString& OutModuleRealpath)
{
    const FString ProjectDirectory = FPaths::GetPath(ProjectRealpath);
    TArray<FString> CandidatePaths = {
        ProjectRealpath,
        FPaths::Combine(ProjectDirectory, TEXT("Config/DefaultEngine.ini")),
        FPaths::Combine(ProjectDirectory, TEXT("Config/DefaultGame.ini")),
        FPaths::Combine(ProjectDirectory, TEXT("Config/DefaultInput.ini")),
        FPaths::Combine(ProjectDirectory, TEXT("Binaries/Mac/libUnrealEditor-CityMaterializationProof.dylib")),
    };
    TArray<TSharedPtr<FJsonValue>> Members;
    for (int32 Index = 0; Index < CandidatePaths.Num(); ++Index)
    {
        FString Realpath;
        FString Digest;
        if (!ResolveRealpath(CandidatePaths[Index], Realpath) || !HashRegularFileRawSha256(Realpath, Digest))
        {
            return false;
        }
        if (Index == CandidatePaths.Num() - 1) OutModuleRealpath = Realpath;
        TSharedPtr<FJsonObject> Member = MakeShared<FJsonObject>();
        Member->SetStringField(TEXT("realpath"), Realpath);
        Member->SetStringField(TEXT("raw_sha256"), Digest);
        Members.Add(MakeShared<FJsonValueObject>(Member));
    }
    OutInventory = MakeShared<FJsonObject>();
    OutInventory->SetStringField(TEXT("inventory_schema"), TEXT("SimultaneousPhysicalDomainProjectModuleInventory.v1"));
    OutInventory->SetArrayField(TEXT("members"), Members);
    OutInventoryDigest = SimultaneousPhysicalDomainJson::Sha256Utf8(
        SimultaneousPhysicalDomainJson::CanonicalizeObject(OutInventory) + TEXT("\n"));
    return true;
}

bool CaptureLoadedImageIdentities(
    const FString& ExecutableRealpath,
    const FString& ModuleRealpath,
    TArray<TSharedPtr<FJsonValue>>& OutImages)
{
    struct FImageIdentity
    {
        FString ReportedPath;
        FString Realpath;
        FString Resolution;
        FString Uuid;
        bool bFilesystemRegular = false;
    };
    TArray<FImageIdentity> Images;
    bool bExecutableObserved = false;
    bool bModuleObserved = false;
    const uint32 Count = _dyld_image_count();
    for (uint32 Index = 0; Index < Count; ++Index)
    {
        const char* RawName = _dyld_get_image_name(Index);
        FString Uuid;
        if (RawName == nullptr || !LoadedMachOUuid(_dyld_get_image_header(Index), Uuid)) return false;
        FImageIdentity Identity;
        Identity.ReportedPath = UTF8_TO_TCHAR(RawName);
        struct stat Info {};
        FString Resolved;
        if (ResolveRealpath(Identity.ReportedPath, Resolved))
        {
            FTCHARToUTF8 ResolvedUtf8(*Resolved);
            if (stat(ResolvedUtf8.Get(), &Info) != 0 || !S_ISREG(Info.st_mode)) return false;
            Identity.Realpath = Resolved;
            Identity.Resolution = TEXT("filesystem_realpath");
            Identity.bFilesystemRegular = true;
        }
        else
        {
            if (FPaths::IsRelative(Identity.ReportedPath)) return false;
            Identity.Realpath = Identity.ReportedPath;
            Identity.Resolution = TEXT("dyld_shared_cache_logical_path");
        }
        Identity.Uuid = Uuid;
        bExecutableObserved |= Identity.Realpath == ExecutableRealpath;
        bModuleObserved |= Identity.Realpath == ModuleRealpath;
        Images.Add(MoveTemp(Identity));
    }
    Images.Sort([](const FImageIdentity& A, const FImageIdentity& B)
    {
        if (A.Realpath != B.Realpath) return A.Realpath < B.Realpath;
        return A.Uuid < B.Uuid;
    });
    FString PreviousKey;
    for (const FImageIdentity& Identity : Images)
    {
        const FString Key = Identity.Realpath + TEXT("\n") + Identity.Uuid;
        if (Key == PreviousKey) continue;
        PreviousKey = Key;
        TSharedPtr<FJsonObject> Item = MakeShared<FJsonObject>();
        Item->SetStringField(TEXT("reported_path"), Identity.ReportedPath);
        Item->SetStringField(TEXT("realpath"), Identity.Realpath);
        Item->SetStringField(TEXT("path_resolution"), Identity.Resolution);
        Item->SetStringField(TEXT("mach_o_uuid"), Identity.Uuid);
        Item->SetBoolField(TEXT("filesystem_regular_file"), Identity.bFilesystemRegular);
        OutImages.Add(MakeShared<FJsonValueObject>(Item));
    }
    return bExecutableObserved && bModuleObserved && OutImages.Num() > 0;
}

bool CaptureInitialActorClassInventory(UWorld* World, TArray<TSharedPtr<FJsonValue>>& OutInventory)
{
    if (World == nullptr) return false;
    TMap<FString, int32> Counts;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        const AActor* Actor = *It;
        if (Actor == nullptr || Actor->GetClass() == nullptr) return false;
        Counts.FindOrAdd(Actor->GetClass()->GetPathName()) += 1;
    }
    TArray<FString> Classes;
    Counts.GetKeys(Classes);
    Classes.Sort();
    for (const FString& ClassPath : Classes)
    {
        TSharedPtr<FJsonObject> Item = MakeShared<FJsonObject>();
        Item->SetStringField(TEXT("class_path"), ClassPath);
        Item->SetNumberField(TEXT("actor_count"), Counts.FindChecked(ClassPath));
        OutInventory.Add(MakeShared<FJsonValueObject>(Item));
    }
    return OutInventory.Num() > 0;
}

bool BuildObservedBindingAndRuntimeProvenance(
    UWorld* World,
    const TSharedPtr<FJsonObject>& Binding,
    TSharedPtr<FJsonObject>& OutRuntimeProvenance,
    FString& OutReason)
{
    using namespace SimultaneousPhysicalDomainJson;
    TArray<FString> Argv;
    TSharedPtr<FJsonObject> EnvironmentAudit;
    TMap<FString, FString> Environment;
    if (!CaptureOriginalArgv(Argv) || !BuildRedactedEnvironmentAudit(EnvironmentAudit, Environment))
    {
        OutReason = TEXT("binding_runtime_launch_surface_unavailable");
        return false;
    }
    uint32 ExecutableBufferSize = 0;
    _NSGetExecutablePath(nullptr, &ExecutableBufferSize);
    TArray<char> ExecutableBuffer;
    ExecutableBuffer.SetNumZeroed(static_cast<int32>(ExecutableBufferSize) + 1);
    if (ExecutableBufferSize == 0 || _NSGetExecutablePath(ExecutableBuffer.GetData(), &ExecutableBufferSize) != 0)
    {
        OutReason = TEXT("binding_executable_path_observation_failed");
        return false;
    }
    FString ExecutableRealpath;
    FString ArgvExecutableRealpath;
    FString ProjectRealpath;
    FString ArgvProjectRealpath;
    if (!ResolveRealpath(UTF8_TO_TCHAR(ExecutableBuffer.GetData()), ExecutableRealpath) ||
        !ResolveRealpath(Argv[0], ArgvExecutableRealpath) || ExecutableRealpath != ArgvExecutableRealpath ||
        !ResolveRealpath(FPaths::GetProjectFilePath(), ProjectRealpath) ||
        !ResolveRealpath(Argv[1], ArgvProjectRealpath) || ProjectRealpath != ArgvProjectRealpath)
    {
        OutReason = TEXT("binding_executable_or_project_realpath_observation_failed");
        return false;
    }

    FString UserDirectory;
    FString WinX;
    for (const FString& Argument : Argv)
    {
        if (Argument.StartsWith(TEXT("-UserDir="))) UserDirectory = Argument.Mid(9);
        if (Argument.StartsWith(TEXT("-WinX="))) WinX = Argument.Mid(6);
    }
    FString UserDirectoryRealpath;
    FString ProcessRootRealpath;
    if (UserDirectory.IsEmpty() || !ResolveRealpath(UserDirectory, UserDirectoryRealpath) ||
        !ResolveRealpath(FPaths::GetPath(UserDirectoryRealpath), ProcessRootRealpath))
    {
        OutReason = TEXT("binding_process_root_observation_failed");
        return false;
    }
    const FString ObservedRole = FPaths::GetCleanFilename(ProcessRootRealpath);
    if ((ObservedRole != TEXT("domain_A") && ObservedRole != TEXT("domain_B")) ||
        (ObservedRole == TEXT("domain_A") ? WinX != TEXT("30") : WinX != TEXT("990")))
    {
        OutReason = TEXT("binding_domain_role_observation_failed");
        return false;
    }

    FString LaunchCwdRealpath;
    const FString* Pwd = Environment.Find(TEXT("PWD"));
    if (Pwd == nullptr || !ResolveRealpath(*Pwd, LaunchCwdRealpath))
    {
        OutReason = TEXT("binding_launch_cwd_observation_failed");
        return false;
    }
    FString ProjectParentRealpath;
    if (!ResolveRealpath(FPaths::Combine(FPaths::GetPath(ProjectRealpath), TEXT("..")), ProjectParentRealpath) ||
        LaunchCwdRealpath != ProjectParentRealpath)
    {
        OutReason = TEXT("binding_launch_cwd_project_relation_failed");
        return false;
    }

    proc_bsdinfo ProcessInfo {};
    const int32 Pid = FPlatformProcess::GetCurrentProcessId();
    if (proc_pidinfo(Pid, PROC_PIDTBSDINFO, 0, &ProcessInfo, sizeof(ProcessInfo)) != sizeof(ProcessInfo) ||
        static_cast<int32>(ProcessInfo.pbi_pid) != Pid)
    {
        OutReason = TEXT("binding_process_start_observation_failed");
        return false;
    }

    FString ExecutableDigest;
    FString ProjectDigest;
    TSharedPtr<FJsonObject> ProjectInventory;
    FString ProjectInventoryDigest;
    FString ModuleRealpath;
    if (!HashRegularFileRawSha256(ExecutableRealpath, ExecutableDigest) ||
        !HashRegularFileRawSha256(ProjectRealpath, ProjectDigest) ||
        !BuildProjectModuleInventory(ProjectRealpath, ProjectInventory, ProjectInventoryDigest, ModuleRealpath))
    {
        OutReason = TEXT("binding_executable_project_inventory_hash_failed");
        return false;
    }

    TSharedPtr<FJsonObject> DescriptorMap;
    TArray<TSharedPtr<FJsonValue>> DescriptorKernelIdentities;
    if (!CaptureDescriptorState(ObservedRole, DescriptorMap, DescriptorKernelIdentities))
    {
        OutReason = TEXT("binding_original_descriptor_observation_failed");
        return false;
    }

    TArray<TSharedPtr<FJsonValue>> ArgvValues;
    for (const FString& Argument : Argv) ArgvValues.Add(MakeShared<FJsonValueString>(Argument));
    const FString ArgvDigest = Sha256Utf8(CanonicalizeValue(MakeShared<FJsonValueArray>(ArgvValues)));
    const FString EnvironmentDigest = Sha256Utf8(CanonicalizeObject(EnvironmentAudit) + TEXT("\n"));
    const FString DescriptorMapDigest = Sha256Utf8(CanonicalizeObject(DescriptorMap) + TEXT("\n"));

    const FString EntryMapIdentity = World != nullptr && World->GetOutermost() != nullptr
        ? World->GetOutermost()->GetName() : TEXT("");
    FString EntryMapRealpath;
    FString EntryMapDigest;
    const FString EntryMapPath = FPaths::Combine(FPaths::EngineContentDir(), TEXT("Maps/Entry.umap"));
    if (EntryMapIdentity != TEXT("/Engine/Maps/Entry") ||
        !SimultaneousPhysicalDomainRuntimeAudit::ResolveAndHashRegularFile(EntryMapPath, EntryMapRealpath, EntryMapDigest))
    {
        OutReason = TEXT("binding_entry_map_observation_failed");
        return false;
    }

    TSharedPtr<FJsonObject> Observed = MakeShared<FJsonObject>();
    Observed->SetStringField(TEXT("binding_schema"), BindingSchema);
    FString WitnessId;
    Binding->TryGetStringField(TEXT("witness_id"), WitnessId);
    Observed->SetStringField(TEXT("proof_scenario"), Scenario);
    Observed->SetStringField(TEXT("witness_id"), WitnessId);
    Observed->SetStringField(TEXT("domain_role"), ObservedRole);
    Observed->SetStringField(TEXT("harness_launch_id"), FString::Printf(TEXT("%s/%s/launch_0001"), *WitnessId, *ObservedRole));
    Observed->SetNumberField(TEXT("pid"), Pid);
    TSharedPtr<FJsonObject> ProcessStart = MakeShared<FJsonObject>();
    ProcessStart->SetNumberField(TEXT("seconds"), static_cast<double>(ProcessInfo.pbi_start_tvsec));
    ProcessStart->SetNumberField(TEXT("microseconds"), static_cast<double>(ProcessInfo.pbi_start_tvusec));
    Observed->SetObjectField(TEXT("macos_process_start"), ProcessStart);
    Observed->SetStringField(TEXT("executable_realpath"), ExecutableRealpath);
    Observed->SetStringField(TEXT("executable_raw_sha256"), ExecutableDigest);
    Observed->SetStringField(TEXT("unreal_engine_build_identity"), FEngineVersion::Current().ToString(EVersionComponent::Branch));
    Observed->SetStringField(TEXT("entry_map_package_identity"), EntryMapIdentity);
    Observed->SetStringField(TEXT("project_realpath"), ProjectRealpath);
    Observed->SetStringField(TEXT("project_raw_sha256"), ProjectDigest);
    Observed->SetStringField(TEXT("project_config_and_module_inventory_raw_sha256"), ProjectInventoryDigest);
    Observed->SetStringField(TEXT("process_root_realpath"), ProcessRootRealpath);
    Observed->SetStringField(TEXT("launch_argv_raw_sha256"), ArgvDigest);
    Observed->SetStringField(TEXT("launch_environment_audit_raw_sha256"), EnvironmentDigest);
    Observed->SetStringField(TEXT("launch_cwd_realpath"), LaunchCwdRealpath);
    Observed->SetStringField(TEXT("inherited_descriptor_map_raw_sha256"), DescriptorMapDigest);
    Observed->SetStringField(TEXT("control_pipe_id"), FString::Printf(TEXT("%s/control/0001"), *ObservedRole));
    Observed->SetStringField(TEXT("structured_output_pipe_id"), FString::Printf(TEXT("%s/stdout/0001"), *ObservedRole));
    Observed->SetStringField(TEXT("diagnostic_pipe_id"), FString::Printf(TEXT("%s/stderr/0001"), *ObservedRole));

    const TCHAR* Fields[] = {
        TEXT("binding_schema"), TEXT("proof_scenario"), TEXT("witness_id"), TEXT("domain_role"), TEXT("harness_launch_id"),
        TEXT("pid"), TEXT("macos_process_start"), TEXT("executable_realpath"), TEXT("executable_raw_sha256"),
        TEXT("unreal_engine_build_identity"), TEXT("entry_map_package_identity"), TEXT("project_realpath"),
        TEXT("project_raw_sha256"), TEXT("project_config_and_module_inventory_raw_sha256"), TEXT("process_root_realpath"),
        TEXT("launch_argv_raw_sha256"), TEXT("launch_environment_audit_raw_sha256"), TEXT("launch_cwd_realpath"),
        TEXT("inherited_descriptor_map_raw_sha256"), TEXT("control_pipe_id"), TEXT("structured_output_pipe_id"),
        TEXT("diagnostic_pipe_id"),
    };
    TArray<TSharedPtr<FJsonValue>> VerificationRows;
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Fields); ++Index)
    {
        const TSharedPtr<FJsonValue>* DeclaredValue = Binding->Values.Find(Fields[Index]);
        const TSharedPtr<FJsonValue>* ObservedValue = Observed->Values.Find(Fields[Index]);
        if (DeclaredValue == nullptr || ObservedValue == nullptr ||
            CanonicalizeValue(*DeclaredValue) != CanonicalizeValue(*ObservedValue))
        {
            UE_LOG(
                LogTemp,
                Error,
                TEXT("SimultaneousPhysicalDomain binding mismatch field=%s declared=%s observed=%s"),
                Fields[Index],
                DeclaredValue == nullptr ? TEXT("<missing>") : *CanonicalizeValue(*DeclaredValue),
                ObservedValue == nullptr ? TEXT("<missing>") : *CanonicalizeValue(*ObservedValue));
            if (FString(Fields[Index]) == TEXT("launch_environment_audit_raw_sha256"))
            {
                UE_LOG(
                    LogTemp,
                    Error,
                    TEXT("SimultaneousPhysicalDomain observed redacted environment audit=%s"),
                    *CanonicalizeObject(EnvironmentAudit));
            }
            OutReason = FString::Printf(TEXT("binding_field_mismatch/%s"), Fields[Index]);
            return false;
        }
        TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("field"), Fields[Index]);
        Row->SetStringField(
            TEXT("verification_mode"),
            Index <= 4 ? TEXT("fixed_schema_or_cross_field_derivation") : TEXT("independent_process_observation"));
        Row->SetBoolField(TEXT("matched"), true);
        VerificationRows.Add(MakeShared<FJsonValueObject>(Row));
    }

    TArray<TSharedPtr<FJsonValue>> LoadedImages;
    TArray<TSharedPtr<FJsonValue>> ActorInventory;
    if (!CaptureLoadedImageIdentities(ExecutableRealpath, ModuleRealpath, LoadedImages) ||
        !CaptureInitialActorClassInventory(World, ActorInventory))
    {
        OutReason = TEXT("runtime_provenance_inventory_capture_failed");
        return false;
    }
    TSharedPtr<FJsonObject> EntryMapFile = MakeShared<FJsonObject>();
    EntryMapFile->SetStringField(TEXT("package_identity"), EntryMapIdentity);
    EntryMapFile->SetStringField(TEXT("realpath"), EntryMapRealpath);
    EntryMapFile->SetStringField(TEXT("raw_sha256"), EntryMapDigest);

    OutRuntimeProvenance = MakeShared<FJsonObject>();
    OutRuntimeProvenance->SetStringField(TEXT("audit_schema"), TEXT("SimultaneousPhysicalDomainRuntimeProvenance.v1"));
    OutRuntimeProvenance->SetStringField(TEXT("proof_scenario"), Scenario);
    OutRuntimeProvenance->SetBoolField(TEXT("captured_before_first_materialization"), true);
    OutRuntimeProvenance->SetObjectField(TEXT("observed_process_binding"), Observed);
    OutRuntimeProvenance->SetArrayField(TEXT("binding_verification_rows"), VerificationRows);
    OutRuntimeProvenance->SetArrayField(TEXT("observed_launch_argv"), ArgvValues);
    OutRuntimeProvenance->SetObjectField(TEXT("redacted_environment_audit"), EnvironmentAudit);
    OutRuntimeProvenance->SetObjectField(TEXT("project_config_and_module_inventory"), ProjectInventory);
    OutRuntimeProvenance->SetObjectField(TEXT("observed_inherited_descriptor_map"), DescriptorMap);
    OutRuntimeProvenance->SetArrayField(TEXT("descriptor_kernel_identities"), DescriptorKernelIdentities);
    OutRuntimeProvenance->SetArrayField(TEXT("loaded_image_identities"), LoadedImages);
    OutRuntimeProvenance->SetArrayField(TEXT("initial_world_actor_class_inventory"), ActorInventory);
    OutRuntimeProvenance->SetObjectField(TEXT("entry_map_file_identity"), EntryMapFile);
    return true;
}
}

namespace SimultaneousPhysicalDomainFault
{
bool InjectAt(
    FSPDInjectedFaultPlan* Plan,
    const TCHAR* Surface,
    const TCHAR* Stage,
    const TCHAR* Edge,
    FString& OutReason)
{
    if (Plan == nullptr || !Plan->bArmed || Plan->bInjected ||
        Plan->Surface != Surface || Plan->Stage != Stage || Plan->Edge != Edge)
    {
        return false;
    }
    Plan->bInjected = true;
    Plan->bBoundaryEntered = true;
    Plan->bBoundaryCompleted = Plan->Edge == TEXT("after") || Plan->Edge == TEXT("at");
    OutReason = FString::Printf(TEXT("injected_fault/%s/%s/%s"), Surface, Stage, Edge);
    return true;
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

bool ASimultaneousPhysicalDomainCommandRouter::VerifyObservableBinding(
    const TSharedPtr<FJsonObject>& Binding,
    TSharedPtr<FJsonObject>& OutRuntimeProvenance,
    FString& OutReason) const
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
    if (!Binding->TryGetStringField(TEXT("domain_role"), DomainRole) ||
        (DomainRole != TEXT("domain_A") && DomainRole != TEXT("domain_B")) ||
        !Binding->TryGetStringField(TEXT("witness_id"), WitnessId) || !IsAllowedWitnessId(WitnessId) ||
        !Binding->TryGetStringField(TEXT("harness_launch_id"), HarnessLaunchId) ||
        HarnessLaunchId != WitnessId + TEXT("/") + DomainRole + TEXT("/launch_0001"))
    {
        OutReason = TEXT("binding_fixed_identity_or_cross_field_mismatch");
        return false;
    }
    return BuildObservedBindingAndRuntimeProvenance(
        GetWorld(), Binding, OutRuntimeProvenance, OutReason);
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
    TSharedPtr<FJsonObject> RuntimeProvenance;
    FString InstanceId;
    if (!Command->TryGetObjectField(TEXT("process_binding"), Binding) || !Binding ||
        !Command->TryGetStringField(TEXT("operational_process_instance_id"), InstanceId) || !IsLowerSha256(InstanceId) ||
        Sha256Utf8(CanonicalizeObject(*Binding)) != InstanceId ||
        !VerifyObservableBinding(*Binding, RuntimeProvenance, OutReason))
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
    (*Binding)->TryGetStringField(TEXT("executable_raw_sha256"), ImmutableBinding.ExecutableRawSha256);
    double PidNumber = 0;
    (*Binding)->TryGetNumberField(TEXT("pid"), PidNumber);
    ImmutableBinding.Pid = static_cast<int32>(PidNumber);

    RuntimeProvenance->SetStringField(TEXT("domain_role"), ImmutableBinding.DomainRole);
    RuntimeProvenance->SetStringField(TEXT("operational_process_instance_id"), ImmutableBinding.OperationalProcessInstanceId);
    RuntimeProvenance->SetStringField(TEXT("process_binding_raw_sha256"), ImmutableBinding.ProcessBindingRawSha256);
    SimultaneousPhysicalDomainRuntimeAudit::Initialize(
        ImmutableBinding.DomainRole,
        ImmutableBinding.OperationalProcessInstanceId,
        ImmutableBinding.ProcessBindingRawSha256);
    EmitStructuredObject(RuntimeProvenance);
    SimultaneousPhysicalDomainRuntimeAudit::RecordStdinCommand(Command);

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

bool ASimultaneousPhysicalDomainCommandRouter::AcceptFaultArm(
    const TSharedPtr<FJsonObject>& Command,
    FString& OutReason)
{
    using namespace SimultaneousPhysicalDomainJson;
    if (bFaultArmAccepted || ImmutableBinding.DomainRole != TEXT("domain_A") ||
        !HasExactKeys(Command, {
            TEXT("command_schema"), TEXT("proof_scenario"), TEXT("domain_role"), TEXT("operation"),
            TEXT("fault_run_id"), TEXT("fault_surface"), TEXT("fault_stage"), TEXT("fault_edge"),
            TEXT("target_head_role")
        }) || !ExactString(Command, TEXT("command_schema"), FaultArmCommandSchema) ||
        !ExactString(Command, TEXT("proof_scenario"), Scenario) ||
        !ExactString(Command, TEXT("domain_role"), TEXT("domain_A")) ||
        !ExactString(Command, TEXT("operation"), TEXT("arm_exact_fault_once")))
    {
        OutReason = TEXT("fault_arm_structure_or_role_invalid");
        return false;
    }

    FString RunId;
    FString Surface;
    FString Stage;
    FString Edge;
    FString HeadRole;
    if (!Command->TryGetStringField(TEXT("fault_run_id"), RunId) ||
        !Command->TryGetStringField(TEXT("fault_surface"), Surface) ||
        !Command->TryGetStringField(TEXT("fault_stage"), Stage) ||
        !Command->TryGetStringField(TEXT("fault_edge"), Edge) ||
        !Command->TryGetStringField(TEXT("target_head_role"), HeadRole))
    {
        OutReason = TEXT("fault_arm_fields_missing");
        return false;
    }

    bool bSequenceValid = false;
    FString ExpectedRunId;
    if (Surface == TEXT("refresh"))
    {
        bSequenceValid = ImmutableBinding.WitnessId == TEXT("f_refresh_fault") &&
            IsRefreshFaultStage(Stage) && (Edge == TEXT("before") || Edge == TEXT("after")) &&
            HeadRole == TEXT("H1") && bLaunchInspectionAccepted && !bRefreshAccepted;
        ExpectedRunId = FString::Printf(TEXT("refresh/H1/%s/%s/domain_A"), *Stage, *Edge);
    }
    else if (Surface == TEXT("physical_observation"))
    {
        const bool bH0Slot = HeadRole == TEXT("H0") && !bLaunchInspectionAccepted && !bRefreshAccepted;
        const bool bH1Slot = HeadRole == TEXT("H1") && bLaunchInspectionAccepted && bRefreshAccepted && !bRefreshInspectionAccepted;
        bSequenceValid = ImmutableBinding.WitnessId == TEXT("f_physical_observation_fault") &&
            IsObservationFaultStage(Stage) && Edge == TEXT("at") && (bH0Slot || bH1Slot);
        ExpectedRunId = FString::Printf(TEXT("physical_observation/%s/%s/at/domain_A"), *HeadRole, *Stage);
    }
    if (!bSequenceValid || RunId != ExpectedRunId)
    {
        OutReason = TEXT("fault_arm_cross_field_or_sequence_invalid");
        return false;
    }

    FaultPlan.FaultRunId = RunId;
    FaultPlan.Surface = Surface;
    FaultPlan.Stage = Stage;
    FaultPlan.Edge = Edge;
    FaultPlan.TargetHeadRole = HeadRole;
    FaultPlan.bArmed = true;
    bFaultArmAccepted = true;
    return true;
}

void ASimultaneousPhysicalDomainCommandRouter::EmitFaultArmReceipt() const
{
    using namespace SimultaneousPhysicalDomainJson;
    TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
    Receipt->SetStringField(TEXT("receipt_schema"), TEXT("SimultaneousPhysicalDomainFaultArmReceipt.v1"));
    Receipt->SetStringField(TEXT("proof_scenario"), Scenario);
    Receipt->SetStringField(TEXT("domain_role"), ImmutableBinding.DomainRole);
    Receipt->SetStringField(TEXT("operational_process_instance_id"), ImmutableBinding.OperationalProcessInstanceId);
    Receipt->SetStringField(TEXT("process_binding_raw_sha256"), ImmutableBinding.ProcessBindingRawSha256);
    Receipt->SetStringField(TEXT("executable_raw_sha256"), ImmutableBinding.ExecutableRawSha256);
    Receipt->SetStringField(TEXT("fault_run_id"), FaultPlan.FaultRunId);
    Receipt->SetStringField(TEXT("fault_surface"), FaultPlan.Surface);
    Receipt->SetStringField(TEXT("fault_stage"), FaultPlan.Stage);
    Receipt->SetStringField(TEXT("fault_edge"), FaultPlan.Edge);
    Receipt->SetStringField(TEXT("target_head_role"), FaultPlan.TargetHeadRole);
    Receipt->SetBoolField(TEXT("armed_once"), true);
    EmitStructuredObject(Receipt);
}

void ASimultaneousPhysicalDomainCommandRouter::EmitInjectedFaultResult(
    const FString& ReceiptOutcome,
    const FString& ObservationOutcome,
    const FString& ReasonCode) const
{
    using namespace SimultaneousPhysicalDomainJson;
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("result_schema"), TEXT("SimultaneousPhysicalDomainInjectedFaultResult.v1"));
    Result->SetStringField(TEXT("proof_scenario"), Scenario);
    Result->SetStringField(TEXT("domain_role"), ImmutableBinding.DomainRole);
    Result->SetStringField(TEXT("operational_process_instance_id"), ImmutableBinding.OperationalProcessInstanceId);
    Result->SetStringField(TEXT("process_binding_raw_sha256"), ImmutableBinding.ProcessBindingRawSha256);
    Result->SetStringField(TEXT("executable_raw_sha256"), ImmutableBinding.ExecutableRawSha256);
    Result->SetStringField(TEXT("fault_run_id"), FaultPlan.FaultRunId);
    Result->SetStringField(TEXT("fault_surface"), FaultPlan.Surface);
    Result->SetStringField(TEXT("fault_stage"), FaultPlan.Stage);
    Result->SetStringField(TEXT("fault_edge"), FaultPlan.Edge);
    Result->SetStringField(TEXT("target_head_role"), FaultPlan.TargetHeadRole);
    Result->SetBoolField(TEXT("boundary_entered"), FaultPlan.bBoundaryEntered);
    Result->SetBoolField(TEXT("boundary_completed"), FaultPlan.bBoundaryCompleted);
    Result->SetStringField(TEXT("local_publication_state"), Adapter != nullptr ? Adapter->GetPublicationState() : TEXT("none"));
    Result->SetStringField(TEXT("represented_hash_if_known"), Adapter != nullptr ? Adapter->GetRepresentedCanonicalHash() : TEXT(""));
    Result->SetStringField(TEXT("materialization_receipt_outcome"), ReceiptOutcome);
    Result->SetStringField(TEXT("physical_observation_outcome"), ObservationOutcome);
    Result->SetStringField(TEXT("reason_code"), ReasonCode);
    EmitStructuredObject(Result);
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

    SimultaneousPhysicalDomainRuntimeAudit::RecordStdinCommand(Command);

    FString Schema;
    Command->TryGetStringField(TEXT("command_schema"), Schema);
    FString Reason;
    TSharedPtr<FJsonObject> Result;
    if (Schema == FaultArmCommandSchema)
    {
        if (!AcceptFaultArm(Command, Reason))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("fault_arm_invocation_read"), Reason);
            return;
        }
        EmitFaultArmReceipt();
        return;
    }
    if (Schema == LocalStepCommandSchema)
    {
        if (ImmutableBinding.WitnessId != TEXT("w3_stale_quarantine") ||
            !bLaunchInspectionAccepted || bRefreshAccepted || bLocalStepAccepted ||
            !HasExactKeys(Command, {
                TEXT("command_schema"), TEXT("proof_scenario"), TEXT("domain_role"),
                TEXT("operation"), TEXT("step_id")
            }) || !ExactString(Command, TEXT("proof_scenario"), Scenario) ||
            !ExactString(Command, TEXT("domain_role"), *ImmutableBinding.DomainRole) ||
            !ExactString(Command, TEXT("operation"), TEXT("execute_nonconsequential_step_once")) ||
            !ExactString(Command, TEXT("step_id"), TEXT("stale_quarantine_step_0001")) ||
            !Adapter->ExecuteNonconsequentialStepOnce(ImmutableBinding, Result, Reason))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("local_nonconsequential_step"), Reason.IsEmpty() ? TEXT("local_step_command_invalid") : Reason);
            return;
        }
        bLocalStepAccepted = true;
        EmitStructuredObject(Result);
        return;
    }
    if (Schema == InspectionCommandSchema)
    {
        if (SimultaneousPhysicalDomainFault::InjectAt(
            &FaultPlan, TEXT("physical_observation"), TEXT("inspection_invocation_read"), TEXT("at"), Reason))
        {
            bProtocolFailed = true;
            EmitInjectedFaultResult(TEXT("not_applicable"), TEXT("not_emitted"), Reason);
            return;
        }
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
        if ((!bExpectedLaunchSlot && !bExpectedRefreshSlot) || !Probe->InspectPublishedRoute(InspectionId, &FaultPlan, Result, Reason))
        {
            bProtocolFailed = true;
            if (FaultPlan.bInjected)
            {
                EmitInjectedFaultResult(TEXT("not_applicable"), TEXT("not_emitted"), Reason);
                return;
            }
            EmitFailure(TEXT("inspection_invocation_read"), Reason.IsEmpty() ? TEXT("inspection_order_or_probe_failure") : Reason);
            return;
        }
        bLaunchInspectionAccepted |= bExpectedLaunchSlot;
        bRefreshInspectionAccepted |= bExpectedRefreshSlot;
        if (SimultaneousPhysicalDomainFault::InjectAt(
            &FaultPlan, TEXT("physical_observation"), TEXT("physical_observation_emission"), TEXT("at"), Reason))
        {
            bProtocolFailed = true;
            EmitInjectedFaultResult(TEXT("not_applicable"), TEXT("not_emitted"), Reason);
            return;
        }
        EmitStructuredObject(Result);
        return;
    }
    if (Schema == RefreshCommandSchema)
    {
        if (SimultaneousPhysicalDomainFault::InjectAt(
            &FaultPlan, TEXT("refresh"), TEXT("invocation_read"), TEXT("before"), Reason))
        {
            bRefreshAccepted = true;
            bProtocolFailed = true;
            EmitInjectedFaultResult(TEXT("not_emitted"), TEXT("not_applicable"), Reason);
            return;
        }
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
        if (SimultaneousPhysicalDomainFault::InjectAt(
            &FaultPlan, TEXT("refresh"), TEXT("invocation_read"), TEXT("after"), Reason))
        {
            bRefreshAccepted = true;
            bProtocolFailed = true;
            EmitInjectedFaultResult(TEXT("not_emitted"), TEXT("not_applicable"), Reason);
            return;
        }
        if (!Adapter->RefreshOnce(ImmutableBinding, &FaultPlan, Result, Reason))
        {
            // A prepublication refresh rejection is not a router protocol
            // failure.  The original process remains available for harness
            // diagnostics and termination, but this proof accepts no retry.
            bRefreshAccepted = true;
            if (FaultPlan.bInjected)
            {
                bProtocolFailed = true;
                EmitInjectedFaultResult(TEXT("not_emitted"), TEXT("not_applicable"), Reason);
                return;
            }
            EmitFailure(TEXT("refresh_rejected_before_publication"), Reason);
            return;
        }
        bRefreshAccepted = true;
        if (SimultaneousPhysicalDomainFault::InjectAt(
            &FaultPlan, TEXT("refresh"), TEXT("materialization_receipt_emission"), TEXT("before"), Reason))
        {
            bProtocolFailed = true;
            EmitInjectedFaultResult(TEXT("not_emitted"), TEXT("not_applicable"), Reason);
            return;
        }
        EmitStructuredObject(Result);
        if (SimultaneousPhysicalDomainFault::InjectAt(
            &FaultPlan, TEXT("refresh"), TEXT("materialization_receipt_emission"), TEXT("after"), Reason))
        {
            bProtocolFailed = true;
            EmitInjectedFaultResult(TEXT("emitted_but_not_harness_accepted"), TEXT("not_applicable"), Reason);
            return;
        }
        if (ImmutableBinding.WitnessId == TEXT("w5_retention_baseline") ||
            ImmutableBinding.WitnessId == TEXT("w5_retention_perturbed"))
        {
            const TSharedPtr<FJsonObject> RetentionObservation =
                Adapter->BuildRetentionExecutionObservation(ImmutableBinding);
            if (!RetentionObservation.IsValid())
            {
                bProtocolFailed = true;
                EmitFailure(TEXT("retained_local_state_attachment"), TEXT("retention_execution_observation_failed"));
                return;
            }
            EmitStructuredObject(RetentionObservation);
        }
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
