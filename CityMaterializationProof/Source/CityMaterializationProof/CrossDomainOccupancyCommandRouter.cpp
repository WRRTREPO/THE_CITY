#include "CrossDomainOccupancyCommandRouter.h"

#include "CrossDomainOccupancyLiveWorldProbe.h"
#include "CrossDomainOccupancyProofAdapter.h"
#include "SimultaneousPhysicalDomainCommandRouter.h"
#include "Dom/JsonObject.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "HAL/PlatformProcess.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "HAL/ThreadSafeBool.h"
#include "Misc/EngineVersion.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Templates/SharedPointer.h"
#include "Tickable.h"

#include <crt_externs.h>
#include <fcntl.h>
#include <libproc.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#include <sys/proc_info.h>
#include <sys/stat.h>
#include <unistd.h>

namespace
{
constexpr TCHAR Scenario[] = TEXT("cross-domain-canonical-occupancy-materialization-v1");
constexpr TCHAR BindingSchema[] = TEXT("CrossDomainOccupancyProcessBinding.v1");
constexpr TCHAR BindSchema[] = TEXT("CrossDomainOccupancyBindInvocation.v1");
constexpr TCHAR MaterializeSchema[] = TEXT("CrossDomainOccupancyMaterializeInvocation.v1");
constexpr TCHAR InspectionSchema[] = TEXT("CrossDomainOccupancyInspectionInvocation.v1");
constexpr TCHAR FaultArmSchema[] = TEXT("CrossDomainOccupancyProcessFaultArmInvocation.v1");
constexpr TCHAR LivenessSchema[] = TEXT("CrossDomainOccupancyLivenessAdversaryInvocation.v1");

FCDOImmutableProcessBinding GRuntimeBinding;
FCDOCommandContext GRuntimeCommand;
int64 GRuntimeTraceSequence = 0;

TSharedPtr<FJsonValue> ObjectValue(const TSharedPtr<FJsonObject>& Object)
{
    return MakeShared<FJsonValueObject>(Object);
}

TSharedPtr<FJsonValue> StringValue(const FString& Value)
{
    return MakeShared<FJsonValueString>(Value);
}

TSharedPtr<FJsonObject> JsonIdentity(const TSharedPtr<FJsonObject>& Value)
{
    if (!Value.IsValid()) return nullptr;
    TSharedPtr<FJsonObject> Identity = MakeShared<FJsonObject>();
    Identity->SetStringField(TEXT("schema_or_type"), [&]()
    {
        for (const TCHAR* Field : {TEXT("receipt_schema"), TEXT("observation_schema"), TEXT("diagnostic_schema")})
        {
            FString Found;
            if (Value->TryGetStringField(Field, Found)) return Found;
        }
        return FString(TEXT("closed_json_object"));
    }());
    Identity->SetStringField(
        TEXT("raw_sha256"),
        CrossDomainOccupancyJson::Sha256Utf8(CrossDomainOccupancyJson::CanonicalizeObject(Value) + TEXT("\n")));
    return Identity;
}

bool IsAllowedWitnessId(const FString& Value)
{
    static const TSet<FString> Values = {
        TEXT("w1_A_B__A_B"), TEXT("w2_B_A__B_A"), TEXT("w3_A_B__B_A"), TEXT("w4_B_A__A_B"),
        TEXT("c1_canonical_completion_independence"), TEXT("c2_positive_Rtransit_absence"),
        TEXT("c3_receipt_only_rejection"), TEXT("c4a_start_guard_open"),
        TEXT("c4b_completion_guard_open"), TEXT("c5_process_replacement"),
        TEXT("af_Rtransit_A_success_B_failure"), TEXT("af_Rtransit_B_success_A_failure"),
        TEXT("af_Rfinal_A_success_B_failure"), TEXT("af_Rfinal_B_success_A_failure"),
        TEXT("fault_head_publication"), TEXT("fault_materialization"), TEXT("fault_live_observation"),
        TEXT("authority_adversary"), TEXT("process_binding_adversary"), TEXT("liveness_adversary"),
        TEXT("replay_repeat")
    };
    return Values.Contains(Value);
}

bool IsMaterializationStage(const FString& Value)
{
    static const TSet<FString> Values = {
        TEXT("M01_receive_and_parse_command"), TEXT("M02_resolve_role_private_bundle_root"),
        TEXT("M03_inventory_exact_three_file_directory"), TEXT("M04_open_and_pre_stat_payload"),
        TEXT("M05_read_and_post_stat_payload"), TEXT("M06_authenticate_and_validate_payload"),
        TEXT("M07_open_and_pre_stat_projection"), TEXT("M08_read_and_post_stat_projection"),
        TEXT("M09_authenticate_and_validate_projection"), TEXT("M10_open_and_pre_stat_invocation"),
        TEXT("M11_read_and_post_stat_invocation"), TEXT("M12_validate_operation_tuple_and_process_binding"),
        TEXT("M13_derive_local_subject_disposition"), TEXT("M14_construct_private_anchor_values"),
        TEXT("M15_construct_private_subject_values"), TEXT("M16_validate_candidate_coherence_and_cardinality"),
        TEXT("M17_begin_publication_linearization_interval"),
        TEXT("M18_destroy_and_verify_predecessor_generation_absent"),
        TEXT("M19_spawn_configure_and_finish_target_subject_set"),
        TEXT("M20_spawn_configure_and_finish_target_anchor"),
        TEXT("M21_enumerate_and_validate_adapter_visible_generation"),
        TEXT("M22_emit_materialization_receipt"), TEXT("M23_router_forward_receipt")
    };
    return Values.Contains(Value);
}

bool IsObservationProcessStage(const FString& Value)
{
    static const TSet<FString> Values = {
        TEXT("O01_receive_and_parse_inspection_command"), TEXT("O02_verify_original_process_binding"),
        TEXT("O03_select_exact_process_bound_game_world"), TEXT("O04_enumerate_all_loaded_level_actor_slots"),
        TEXT("O05_classify_all_phase4_relevant_actor_rows"), TEXT("O06_inventory_all_pawn_controller_and_input_rows"),
        TEXT("O07_sort_and_cross_check_counts_with_lists"), TEXT("O08_construct_closed_live_observation"),
        TEXT("O09_emit_live_observation"), TEXT("O10_router_forward_live_observation")
    };
    return Values.Contains(Value);
}

bool IsInspectionId(const FString& Value)
{
    static const TSet<FString> Values = {
        TEXT("inspection_0001"), TEXT("inspection_0002"), TEXT("inspection_0003"),
        TEXT("inspection_0004"), TEXT("inspection_0005"), TEXT("inspection_0006"),
        TEXT("inspection_0007"), TEXT("inspection_0008"), TEXT("inspection_0009"),
        TEXT("inspection_c1_terminal_0001"), TEXT("inspection_c2_rejection_0001"),
        TEXT("inspection_c3_rejection_0001")
    };
    return Values.Contains(Value);
}

bool ExactInteger(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, int32& Out)
{
    double Value = 0;
    if (!Object.IsValid() || !Object->TryGetNumberField(Field, Value) || !FMath::IsFinite(Value) ||
        Value != FMath::FloorToDouble(Value) || Value < 0 || Value > MAX_int32) return false;
    Out = static_cast<int32>(Value);
    return true;
}

bool RealpathOf(const FString& Input, FString& Out)
{
    FTCHARToUTF8 InputUtf8(*Input);
    char Buffer[PATH_MAX] {};
    if (realpath(InputUtf8.Get(), Buffer) == nullptr) return false;
    Out = UTF8_TO_TCHAR(Buffer);
    return true;
}

TSharedPtr<FJsonObject> RedactedEnvironmentAudit()
{
    TArray<TSharedPtr<FJsonValue>> Entries;
    TArray<FString> Rows;
    char*** EnvironmentPointer = _NSGetEnviron();
    if (EnvironmentPointer != nullptr && *EnvironmentPointer != nullptr)
    {
        for (char** Cursor = *EnvironmentPointer; *Cursor != nullptr; ++Cursor)
        {
            Rows.Add(UTF8_TO_TCHAR(*Cursor));
        }
    }
    Rows.Sort([](const FString& A, const FString& B)
    {
        return FCString::Strcmp(*A.Left(A.Find(TEXT("="))), *B.Left(B.Find(TEXT("=")))) < 0;
    });
    for (const FString& Row : Rows)
    {
        int32 Equal = INDEX_NONE;
        if (!Row.FindChar('=', Equal) || Equal <= 0) continue;
        TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
        Entry->SetStringField(TEXT("key"), Row.Left(Equal));
        Entry->SetStringField(TEXT("value_raw_sha256"), CrossDomainOccupancyJson::Sha256Utf8(Row.Mid(Equal + 1)));
        Entries.Add(ObjectValue(Entry));
    }
    TSharedPtr<FJsonObject> Audit = MakeShared<FJsonObject>();
    Audit->SetStringField(TEXT("audit_schema"), TEXT("CrossDomainOccupancyLaunchEnvironmentAudit.v1"));
    Audit->SetBoolField(TEXT("plaintext_values_released"), false);
    Audit->SetArrayField(TEXT("proof_semantic_key_allowlist"), {});
    Audit->SetArrayField(TEXT("sorted_entries"), Entries);
    return Audit;
}

TSharedPtr<FJsonObject> DescriptorMap(const FString& Role, TArray<TSharedPtr<FJsonValue>>& OutKernelRows)
{
    TSharedPtr<FJsonObject> Map = MakeShared<FJsonObject>();
    Map->SetStringField(TEXT("descriptor_map_schema"), TEXT("CrossDomainOccupancyInheritedDescriptorMap.v1"));
    for (int Descriptor = 0; Descriptor <= 2; ++Descriptor)
    {
        const TCHAR* Field = Descriptor == 0 ? TEXT("fd_0") : (Descriptor == 1 ? TEXT("fd_1") : TEXT("fd_2"));
        const TCHAR* Name = Descriptor == 0 ? TEXT("control") : (Descriptor == 1 ? TEXT("stdout") : TEXT("stderr"));
        const TCHAR* Endpoint = Descriptor == 0 ? TEXT("original_control_pipe_read_endpoint") :
            (Descriptor == 1 ? TEXT("original_structured_output_pipe_write_endpoint") : TEXT("original_diagnostic_pipe_write_endpoint"));
        TSharedPtr<FJsonObject> Logical = MakeShared<FJsonObject>();
        Logical->SetStringField(TEXT("pipe_id"), FString::Printf(TEXT("%s/%s/0001"), *Role, Name));
        Logical->SetStringField(TEXT("role"), Endpoint);
        Map->SetObjectField(Field, Logical);

        struct stat Info {};
        const int Flags = fcntl(Descriptor, F_GETFL);
        TSharedPtr<FJsonObject> Kernel = MakeShared<FJsonObject>();
        Kernel->SetStringField(TEXT("access_mode"), (Flags & O_ACCMODE) == O_RDONLY ? TEXT("read_only") : TEXT("write_only"));
        Kernel->SetStringField(TEXT("device"), fstat(Descriptor, &Info) == 0 ?
            FString::Printf(TEXT("%llu"), static_cast<unsigned long long>(Info.st_dev)) : TEXT("unavailable"));
        Kernel->SetNumberField(TEXT("fd"), Descriptor);
        Kernel->SetStringField(TEXT("file_type"), S_ISFIFO(Info.st_mode) ? TEXT("fifo") : TEXT("unexpected"));
        Kernel->SetStringField(TEXT("inode"), FString::Printf(TEXT("%llu"), static_cast<unsigned long long>(Info.st_ino)));
        OutKernelRows.Add(ObjectValue(Kernel));
    }
    Map->SetStringField(TEXT("all_other_descriptors_at_exec"), TEXT("closed"));
    return Map;
}

TSharedPtr<FJsonObject> ProjectInventory(const FString& ProjectRealpath)
{
    TArray<FString> Paths = {
        ProjectRealpath,
        FPaths::Combine(FPaths::GetPath(ProjectRealpath), TEXT("Config/DefaultEngine.ini")),
        FPaths::Combine(FPaths::GetPath(ProjectRealpath), TEXT("Config/DefaultGame.ini")),
        FPaths::Combine(FPaths::GetPath(ProjectRealpath), TEXT("Config/DefaultInput.ini")),
        FModuleManager::Get().GetModuleFilename(TEXT("CityMaterializationProof"))
    };
    TArray<TSharedPtr<FJsonValue>> Members;
    for (const FString& Path : Paths)
    {
        FString Realpath;
        FString Digest;
        if (!SimultaneousPhysicalDomainRuntimeAudit::ResolveAndHashRegularFile(Path, Realpath, Digest)) return nullptr;
        TSharedPtr<FJsonObject> Member = MakeShared<FJsonObject>();
        Member->SetStringField(TEXT("raw_sha256"), Digest);
        Member->SetStringField(TEXT("realpath"), Realpath);
        Members.Add(ObjectValue(Member));
    }
    TSharedPtr<FJsonObject> Inventory = MakeShared<FJsonObject>();
    Inventory->SetStringField(TEXT("inventory_schema"), TEXT("CrossDomainOccupancyProjectConfigAndModuleInventory.v1"));
    Inventory->SetArrayField(TEXT("members"), Members);
    return Inventory;
}

TArray<TSharedPtr<FJsonValue>> ActorInventory(UWorld* World)
{
    TMap<FString, int32> Counts;
    if (World != nullptr)
    {
        for (ULevel* Level : World->GetLevels())
        {
            if (Level == nullptr) continue;
            for (const TObjectPtr<AActor>& Slot : Level->Actors)
            {
                if (AActor* Actor = Slot.Get()) Counts.FindOrAdd(Actor->GetClass()->GetPathName()) += 1;
            }
        }
    }
    TArray<FString> Names;
    Counts.GetKeys(Names);
    Names.Sort();
    TArray<TSharedPtr<FJsonValue>> Rows;
    for (const FString& Name : Names)
    {
        TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetNumberField(TEXT("actor_count"), Counts[Name]);
        Row->SetStringField(TEXT("class_path"), Name);
        Rows.Add(ObjectValue(Row));
    }
    return Rows;
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

bool LoadedImageInventory(
    const FString& ExecutableRealpath,
    const FString& ModuleRealpath,
    TArray<TSharedPtr<FJsonValue>>& OutRows)
{
    struct FLoadedImageRow
    {
        FString ReportedPath;
        FString ResolvedPath;
        FString PathResolution;
        FString MachOUuid;
        bool bFilesystemRegular = false;
    };
    TArray<FLoadedImageRow> Images;
    bool bExecutableObserved = false;
    bool bModuleObserved = false;
    const uint32 Count = _dyld_image_count();
    for (uint32 Index = 0; Index < Count; ++Index)
    {
        const char* Reported = _dyld_get_image_name(Index);
        FString MachOUuid;
        if (Reported == nullptr || !LoadedMachOUuid(_dyld_get_image_header(Index), MachOUuid)) return false;
        FLoadedImageRow Row;
        Row.ReportedPath = UTF8_TO_TCHAR(Reported);
        Row.MachOUuid = MachOUuid;
        FTCHARToUTF8 ReportedUtf8(*Row.ReportedPath);
        char Resolved[PATH_MAX] {};
        struct stat Info {};
        if (realpath(ReportedUtf8.Get(), Resolved) != nullptr && stat(Resolved, &Info) == 0 && S_ISREG(Info.st_mode))
        {
            Row.ResolvedPath = UTF8_TO_TCHAR(Resolved);
            Row.PathResolution = TEXT("filesystem_realpath");
            Row.bFilesystemRegular = true;
        }
        else
        {
            if (FPaths::IsRelative(Row.ReportedPath)) return false;
            Row.ResolvedPath = Row.ReportedPath;
            Row.PathResolution = TEXT("dyld_shared_cache_logical_path");
        }
        bExecutableObserved |= Row.ResolvedPath == ExecutableRealpath;
        bModuleObserved |= Row.ResolvedPath == ModuleRealpath;
        Images.Add(MoveTemp(Row));
    }
    Images.Sort([](const FLoadedImageRow& A, const FLoadedImageRow& B)
    {
        const int32 RealpathOrder = A.ResolvedPath.Compare(B.ResolvedPath, ESearchCase::CaseSensitive);
        if (RealpathOrder != 0) return RealpathOrder < 0;
        const int32 UuidOrder = A.MachOUuid.Compare(B.MachOUuid, ESearchCase::CaseSensitive);
        if (UuidOrder != 0) return UuidOrder < 0;
        return A.ReportedPath.Compare(B.ReportedPath, ESearchCase::CaseSensitive) < 0;
    });
    FString Previous;
    for (const FLoadedImageRow& Image : Images)
    {
        const FString Identity = Image.ResolvedPath + TEXT("\n") + Image.MachOUuid + TEXT("\n") + Image.ReportedPath;
        if (Identity == Previous) continue;
        Previous = Identity;
        TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetBoolField(TEXT("filesystem_regular_file"), Image.bFilesystemRegular);
        Row->SetStringField(TEXT("mach_o_uuid"), Image.MachOUuid);
        Row->SetStringField(TEXT("path_resolution"), Image.PathResolution);
        Row->SetStringField(TEXT("realpath"), Image.ResolvedPath);
        Row->SetStringField(TEXT("reported_path"), Image.ReportedPath);
        OutRows.Add(ObjectValue(Row));
    }
    return bExecutableObserved && bModuleObserved && OutRows.Num() > 0;
}

void SetNullOrString(TSharedPtr<FJsonObject>& Object, const TCHAR* Field, const FString& Value)
{
    if (Value.IsEmpty()) Object->SetField(Field, MakeShared<FJsonValueNull>());
    else Object->SetStringField(Field, Value);
}
}

namespace CrossDomainOccupancyJson
{
bool ParseCanonicalObject(const FString& Canonical, TSharedPtr<FJsonObject>& OutObject)
{
    return SimultaneousPhysicalDomainJson::ParseCanonicalObject(Canonical, OutObject);
}

FString CanonicalizeObject(const TSharedPtr<FJsonObject>& Object)
{
    return SimultaneousPhysicalDomainJson::CanonicalizeObject(Object);
}

FString CanonicalizeValue(const TSharedPtr<FJsonValue>& Value)
{
    return SimultaneousPhysicalDomainJson::CanonicalizeValue(Value);
}

FString Sha256Utf8(const FString& Value)
{
    return SimultaneousPhysicalDomainJson::Sha256Utf8(Value);
}

FString Sha256Bytes(const TArray<uint8>& Bytes)
{
    return SimultaneousPhysicalDomainJson::Sha256Bytes(Bytes);
}

bool HasExactKeys(const TSharedPtr<FJsonObject>& Object, std::initializer_list<const TCHAR*> Keys)
{
    return SimultaneousPhysicalDomainJson::HasExactKeys(Object, Keys);
}

bool ExactString(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, const TCHAR* Expected)
{
    return SimultaneousPhysicalDomainJson::ExactString(Object, Field, Expected);
}

bool IsLowerSha256(const FString& Value)
{
    return SimultaneousPhysicalDomainJson::IsLowerSha256(Value);
}

void EmitStructuredObject(const TSharedPtr<FJsonObject>& Object)
{
    SimultaneousPhysicalDomainJson::EmitStructuredObject(Object);
}
}

namespace CrossDomainOccupancyRuntime
{
void Initialize(const FCDOImmutableProcessBinding& Binding)
{
    GRuntimeBinding = Binding;
    GRuntimeTraceSequence = 0;
}

void BeginCommand(const FCDOCommandContext& Context)
{
    GRuntimeCommand = Context;
}

void EmitStage(
    const FString& StageId,
    const FString& StageEdge,
    const FString& PublicationGeneration,
    const FString& RepresentedCanonicalHash,
    const TArray<TSharedPtr<FJsonValue>>& InputRows,
    const TSharedPtr<FJsonObject>& OutputIdentity)
{
    if (GRuntimeBinding.OperationalProcessInstanceId.IsEmpty()) return;
    TSharedPtr<FJsonObject> Event = MakeShared<FJsonObject>();
    Event->SetStringField(TEXT("command_raw_sha256"), GRuntimeCommand.CommandRawSha256);
    Event->SetNumberField(TEXT("command_sequence"), GRuntimeCommand.CommandSequence);
    Event->SetStringField(TEXT("command_schema"), GRuntimeCommand.CommandSchema);
    Event->SetStringField(TEXT("domain_role"), GRuntimeBinding.DomainRole);
    Event->SetArrayField(TEXT("input_member_device_inode_size_sha256"), InputRows);
    Event->SetNumberField(TEXT("monotonic_process_local_counter"), GRuntimeTraceSequence);
    Event->SetStringField(TEXT("occurrence_id"), FString::Printf(
        TEXT("%s/%s/%s"), *GRuntimeBinding.HarnessLaunchId, *GRuntimeCommand.OperationId, *StageId));
    Event->SetStringField(TEXT("operation_id"), GRuntimeCommand.OperationId);
    Event->SetStringField(TEXT("operational_process_instance_id"), GRuntimeBinding.OperationalProcessInstanceId);
    Event->SetField(TEXT("output_identity"), OutputIdentity.IsValid() ? ObjectValue(JsonIdentity(OutputIdentity)) : MakeShared<FJsonValueNull>());
    Event->SetStringField(TEXT("process_binding_raw_sha256"), GRuntimeBinding.ProcessBindingRawSha256);
    SetNullOrString(Event, TEXT("publication_generation"), PublicationGeneration);
    SetNullOrString(Event, TEXT("represented_canonical_hash"), RepresentedCanonicalHash);
    Event->SetStringField(TEXT("stage_edge"), StageEdge);
    Event->SetStringField(TEXT("stage_id"), StageId);
    Event->SetStringField(TEXT("trace_schema"), TEXT("CrossDomainOccupancyRuntimeTraceEvent.v1"));
    Event->SetNumberField(TEXT("trace_sequence"), GRuntimeTraceSequence++);
    CrossDomainOccupancyJson::EmitStructuredObject(Event);
}

bool InjectAt(FCDOInjectedFaultPlan* Plan, const FString& StageId, const FString& Edge, FString& OutReason)
{
    if (Plan == nullptr || !Plan->bArmed || Plan->bInjected || Plan->StageId != StageId || Plan->Edge != Edge) return false;
    Plan->bInjected = true;
    OutReason = FString::Printf(TEXT("injected_%s_%s"), *StageId, *Edge);
    EmitStage(StageId, TEXT("fault_injected"), TEXT(""), TEXT(""));
    return true;
}
}

class FCDOInputRunnable final : public FRunnable
{
public:
    explicit FCDOInputRunnable(TQueue<FString, EQueueMode::Mpsc>& InQueue) : Queue(InQueue) {}

    virtual uint32 Run() override
    {
        TArray<uint8> Pending;
        Pending.Reserve(64 * 1024);
        uint8 Buffer[4096];
        while (!bStop)
        {
            const ssize_t Count = ::read(STDIN_FILENO, Buffer, sizeof(Buffer));
            if (Count <= 0) break;
            for (ssize_t Index = 0; Index < Count; ++Index)
            {
                const uint8 Byte = Buffer[Index];
                if (Byte == '\n')
                {
                    if (Pending.Num() > 0 && !Pending.Contains(static_cast<uint8>('\r')))
                    {
                        FUTF8ToTCHAR Converted(reinterpret_cast<const ANSICHAR*>(Pending.GetData()), Pending.Num());
                        const FString Line(Converted.Length(), Converted.Get());
                        const bool bCloseOriginalControlAfterQueue =
                            Line.Contains(TEXT("\"case_id\":\"LV04\"")) &&
                            Line.Contains(TEXT("\"action_id\":\"close_control_read_endpoint\"")) &&
                            Line.Contains(TEXT("\"liveness_invocation_schema\":\"CrossDomainOccupancyLivenessAdversaryInvocation.v1\""));
                        Queue.Enqueue(Line);
                        if (bCloseOriginalControlAfterQueue)
                        {
                            close(STDIN_FILENO);
                            return 0;
                        }
                    }
                    else Queue.Enqueue(TEXT(""));
                    Pending.Reset();
                }
                else if (Pending.Num() < 16 * 1024 * 1024) Pending.Add(Byte);
                else { Pending.Reset(); Queue.Enqueue(TEXT("")); }
            }
        }
        return 0;
    }

    virtual void Stop() override { bStop = true; }

private:
    TQueue<FString, EQueueMode::Mpsc>& Queue;
    FThreadSafeBool bStop = false;
};

FCrossDomainOccupancyCommandRouter::FCrossDomainOccupancyCommandRouter() = default;

FCrossDomainOccupancyCommandRouter::~FCrossDomainOccupancyCommandRouter()
{
    if (TickerHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
    if (InputRunnable != nullptr) InputRunnable->Stop();
}

bool FCrossDomainOccupancyCommandRouter::Start(UWorld* InWorld)
{
    if (InWorld == nullptr || World.IsValid()) return false;
    World = InWorld;
    InputRunnable = new FCDOInputRunnable(PendingLines);
    InputThread = FRunnableThread::Create(InputRunnable, TEXT("CrossDomainOccupancyStdin"));
    if (InputThread == nullptr) return false;
    TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateRaw(this, &FCrossDomainOccupancyCommandRouter::Pump), 0.01f);
    return true;
}

bool FCrossDomainOccupancyCommandRouter::Pump(float DeltaSeconds)
{
    (void)DeltaSeconds;
    FString Line;
    while (PendingLines.Dequeue(Line)) HandleLine(Line);
    return true;
}

bool FCrossDomainOccupancyCommandRouter::VerifyObservableBinding(
    const TSharedPtr<FJsonObject>& Candidate,
    TSharedPtr<FJsonObject>& OutRuntimeProvenance,
    FString& OutReason) const
{
    using namespace CrossDomainOccupancyJson;
    if (!HasExactKeys(Candidate, {
        TEXT("binding_schema"), TEXT("proof_scenario"), TEXT("witness_id"), TEXT("domain_role"),
        TEXT("harness_launch_id"), TEXT("pid"), TEXT("macos_process_start"), TEXT("executable_realpath"),
        TEXT("executable_raw_sha256"), TEXT("unreal_engine_build_identity"), TEXT("entry_map_package_identity"),
        TEXT("project_realpath"), TEXT("project_raw_sha256"),
        TEXT("project_config_and_module_inventory_raw_sha256"), TEXT("process_root_realpath"),
        TEXT("launch_argv_raw_sha256"), TEXT("launch_environment_audit_raw_sha256"), TEXT("launch_cwd_realpath"),
        TEXT("inherited_descriptor_map_raw_sha256"), TEXT("control_pipe_id"),
        TEXT("structured_output_pipe_id"), TEXT("diagnostic_pipe_id")
    }) || !ExactString(Candidate, TEXT("binding_schema"), BindingSchema) ||
        !ExactString(Candidate, TEXT("proof_scenario"), Scenario))
    {
        OutReason = TEXT("binding_structure_mismatch");
        return false;
    }

    int Argc = *_NSGetArgc();
    char** Argv = *_NSGetArgv();
    TArray<FString> Arguments;
    for (int Index = 0; Index < Argc; ++Index) Arguments.Add(UTF8_TO_TCHAR(Argv[Index]));
    if (Arguments.Num() != 13 || Arguments[2] != TEXT("-game") || Arguments[3] != TEXT("-Multiprocess") ||
        Arguments[4] != TEXT("-CrossDomainOccupancyProof") || Arguments[5] != TEXT("-NoSplash") ||
        Arguments[6] != TEXT("-Windowed") || Arguments[7] != TEXT("-ResX=900") || Arguments[8] != TEXT("-ResY=650") ||
        Arguments[10] != TEXT("-WinY=60"))
    {
        OutReason = TEXT("launch_argv_exact_surface_mismatch");
        return false;
    }
    FString UserArgument;
    FString LogArgument;
    for (const FString& Argument : Arguments)
    {
        if (Argument.StartsWith(TEXT("-UserDir="))) UserArgument = Argument.Mid(9);
        if (Argument.StartsWith(TEXT("-abslog="))) LogArgument = Argument.Mid(8);
    }
    FString UserRealpath;
    if (!RealpathOf(UserArgument, UserRealpath))
    {
        OutReason = TEXT("process_root_user_path_unresolvable");
        return false;
    }
    const FString ProcessRoot = FPaths::GetPath(UserRealpath);
    const FString ObservedRole = FPaths::GetCleanFilename(ProcessRoot);
    const FString ObservedWitness = FPaths::GetCleanFilename(FPaths::GetPath(ProcessRoot));
    const FString ExpectedLog = FPaths::Combine(ProcessRoot, TEXT("diagnostic/UnrealEditor.log"));
    if ((ObservedRole != TEXT("domain_A") && ObservedRole != TEXT("domain_B")) || !IsAllowedWitnessId(ObservedWitness) ||
        LogArgument != ExpectedLog || Arguments[9] != (ObservedRole == TEXT("domain_A") ? TEXT("-WinX=30") : TEXT("-WinX=990")))
    {
        OutReason = TEXT("binding_fixed_identity_or_root_relationship_mismatch");
        return false;
    }

    FString ExecutableRealpath;
    FString ExecutableDigest;
    FString ProjectRealpath;
    FString ProjectDigest;
    if (!SimultaneousPhysicalDomainRuntimeAudit::ResolveAndHashRegularFile(Arguments[0], ExecutableRealpath, ExecutableDigest) ||
        !SimultaneousPhysicalDomainRuntimeAudit::ResolveAndHashRegularFile(Arguments[1], ProjectRealpath, ProjectDigest))
    {
        OutReason = TEXT("executable_or_project_identity_failed");
        return false;
    }
    TSharedPtr<FJsonObject> Project = ProjectInventory(ProjectRealpath);
    TSharedPtr<FJsonObject> Environment = RedactedEnvironmentAudit();
    TArray<TSharedPtr<FJsonValue>> KernelDescriptors;
    TSharedPtr<FJsonObject> Descriptors = DescriptorMap(ObservedRole, KernelDescriptors);
    if (!Project.IsValid())
    {
        OutReason = TEXT("project_inventory_failed");
        return false;
    }
    FString ModuleRealpath;
    FString ModuleDigest;
    if (!SimultaneousPhysicalDomainRuntimeAudit::ResolveAndHashRegularFile(
            FModuleManager::Get().GetModuleFilename(TEXT("CityMaterializationProof")),
            ModuleRealpath,
            ModuleDigest))
    {
        OutReason = TEXT("module_identity_failed");
        return false;
    }
    TArray<TSharedPtr<FJsonValue>> LoadedImages;
    if (!LoadedImageInventory(ExecutableRealpath, ModuleRealpath, LoadedImages))
    {
        OutReason = TEXT("loaded_image_inventory_missing_bound_executable_or_module");
        return false;
    }
    TArray<TSharedPtr<FJsonValue>> ArgvValues;
    for (const FString& Argument : Arguments) ArgvValues.Add(StringValue(Argument));
    const TSharedPtr<FJsonValue> ArgvJson = MakeShared<FJsonValueArray>(ArgvValues);

    proc_bsdinfo Info {};
    const int32 Pid = static_cast<int32>(getpid());
    if (proc_pidinfo(Pid, PROC_PIDTBSDINFO, 0, &Info, sizeof(Info)) != sizeof(Info))
    {
        OutReason = TEXT("process_birth_observation_failed");
        return false;
    }
    FString LaunchPwd;
    char*** EnvironmentPointer = _NSGetEnviron();
    if (EnvironmentPointer != nullptr && *EnvironmentPointer != nullptr)
    {
        for (char** Cursor = *EnvironmentPointer; *Cursor != nullptr; ++Cursor)
        {
            const FString Row(UTF8_TO_TCHAR(*Cursor));
            if (Row.StartsWith(TEXT("PWD=")))
            {
                LaunchPwd = Row.Mid(4);
                break;
            }
        }
    }
    FString CwdRealpath;
    if (LaunchPwd.IsEmpty() || !RealpathOf(LaunchPwd, CwdRealpath))
    {
        OutReason = TEXT("launch_cwd_observation_failed");
        return false;
    }

    TSharedPtr<FJsonObject> Start = MakeShared<FJsonObject>();
    Start->SetNumberField(TEXT("microseconds"), static_cast<double>(Info.pbi_start_tvusec));
    Start->SetNumberField(TEXT("seconds"), static_cast<double>(Info.pbi_start_tvsec));
    TSharedPtr<FJsonObject> Observed = MakeShared<FJsonObject>();
    Observed->SetStringField(TEXT("binding_schema"), BindingSchema);
    Observed->SetStringField(TEXT("control_pipe_id"), FString::Printf(TEXT("%s/control/0001"), *ObservedRole));
    Observed->SetStringField(TEXT("diagnostic_pipe_id"), FString::Printf(TEXT("%s/stderr/0001"), *ObservedRole));
    Observed->SetStringField(TEXT("domain_role"), ObservedRole);
    Observed->SetStringField(TEXT("entry_map_package_identity"), TEXT("/Engine/Maps/Entry"));
    Observed->SetStringField(TEXT("executable_raw_sha256"), ExecutableDigest);
    Observed->SetStringField(TEXT("executable_realpath"), ExecutableRealpath);
    Observed->SetStringField(TEXT("harness_launch_id"), FString::Printf(TEXT("%s/%s/launch_0001"), *ObservedWitness, *ObservedRole));
    Observed->SetStringField(TEXT("inherited_descriptor_map_raw_sha256"), Sha256Utf8(CanonicalizeObject(Descriptors) + TEXT("\n")));
    Observed->SetStringField(TEXT("launch_argv_raw_sha256"), Sha256Utf8(CanonicalizeValue(ArgvJson)));
    Observed->SetStringField(TEXT("launch_cwd_realpath"), CwdRealpath);
    Observed->SetStringField(TEXT("launch_environment_audit_raw_sha256"), Sha256Utf8(CanonicalizeObject(Environment) + TEXT("\n")));
    Observed->SetObjectField(TEXT("macos_process_start"), Start);
    Observed->SetNumberField(TEXT("pid"), Pid);
    Observed->SetStringField(TEXT("process_root_realpath"), ProcessRoot);
    Observed->SetStringField(TEXT("project_config_and_module_inventory_raw_sha256"), Sha256Utf8(CanonicalizeObject(Project) + TEXT("\n")));
    Observed->SetStringField(TEXT("project_raw_sha256"), ProjectDigest);
    Observed->SetStringField(TEXT("project_realpath"), ProjectRealpath);
    Observed->SetStringField(TEXT("proof_scenario"), Scenario);
    Observed->SetStringField(TEXT("structured_output_pipe_id"), FString::Printf(TEXT("%s/stdout/0001"), *ObservedRole));
    Observed->SetStringField(TEXT("unreal_engine_build_identity"), FEngineVersion::Current().ToString(EVersionComponent::Branch));
    Observed->SetStringField(TEXT("witness_id"), ObservedWitness);
    for (const auto& Pair : Observed->Values)
    {
        const TSharedPtr<FJsonValue>* CandidateValue = Candidate->Values.Find(Pair.Key);
        if (CandidateValue == nullptr || CanonicalizeValue(Pair.Value) != CanonicalizeValue(*CandidateValue))
        {
            OutReason = FString::Printf(TEXT("binding_field_mismatch_%s"), *Pair.Key);
            return false;
        }
    }
    if (CanonicalizeObject(Observed) != CanonicalizeObject(Candidate))
    {
        OutReason = TEXT("binding_independent_observation_mismatch");
        return false;
    }

    static const TCHAR* Fields[] = {
        TEXT("binding_schema"), TEXT("proof_scenario"), TEXT("witness_id"), TEXT("domain_role"),
        TEXT("harness_launch_id"), TEXT("pid"), TEXT("macos_process_start"), TEXT("executable_realpath"),
        TEXT("executable_raw_sha256"), TEXT("unreal_engine_build_identity"), TEXT("entry_map_package_identity"),
        TEXT("project_realpath"), TEXT("project_raw_sha256"), TEXT("project_config_and_module_inventory_raw_sha256"),
        TEXT("process_root_realpath"), TEXT("launch_argv_raw_sha256"), TEXT("launch_environment_audit_raw_sha256"),
        TEXT("launch_cwd_realpath"), TEXT("inherited_descriptor_map_raw_sha256"), TEXT("control_pipe_id"),
        TEXT("structured_output_pipe_id"), TEXT("diagnostic_pipe_id")
    };
    static const TCHAR* VerificationModes[] = {
        TEXT("compiled_constant_identity"), TEXT("compiled_constant_identity"),
        TEXT("harness_frozen_launch_plan_identity"), TEXT("harness_frozen_launch_plan_identity"),
        TEXT("harness_frozen_launch_plan_identity"),
        TEXT("independent_process_observation"), TEXT("independent_process_observation"),
        TEXT("independent_process_observation"), TEXT("independent_process_observation"),
        TEXT("independent_process_observation"), TEXT("independent_process_observation"),
        TEXT("independent_process_observation"), TEXT("independent_process_observation"),
        TEXT("independent_process_observation"),
        TEXT("harness_created_and_independently_reobserved_identity"),
        TEXT("independent_process_observation"), TEXT("independent_process_observation"),
        TEXT("independent_process_observation"), TEXT("independent_process_observation"),
        TEXT("harness_created_and_independently_reobserved_identity"),
        TEXT("harness_created_and_independently_reobserved_identity"),
        TEXT("harness_created_and_independently_reobserved_identity")
    };
    static_assert(UE_ARRAY_COUNT(Fields) == UE_ARRAY_COUNT(VerificationModes), "binding mode table must be field-complete");
    TArray<TSharedPtr<FJsonValue>> VerificationRows;
    for (int Index = 0; Index < UE_ARRAY_COUNT(Fields); ++Index)
    {
        TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("field"), Fields[Index]);
        Row->SetBoolField(TEXT("matched"), true);
        Row->SetStringField(TEXT("verification_mode"), VerificationModes[Index]);
        VerificationRows.Add(ObjectValue(Row));
    }
    OutRuntimeProvenance = MakeShared<FJsonObject>();
    OutRuntimeProvenance->SetStringField(TEXT("audit_schema"), TEXT("CrossDomainOccupancyRuntimeProvenance.v1"));
    OutRuntimeProvenance->SetArrayField(TEXT("binding_verification_rows"), VerificationRows);
    OutRuntimeProvenance->SetBoolField(TEXT("captured_before_first_materialization"), true);
    OutRuntimeProvenance->SetArrayField(TEXT("descriptor_kernel_identities"), KernelDescriptors);
    OutRuntimeProvenance->SetStringField(TEXT("domain_role"), ObservedRole);
    OutRuntimeProvenance->SetArrayField(TEXT("initial_world_actor_class_inventory"), ActorInventory(World.Get()));
    OutRuntimeProvenance->SetArrayField(TEXT("loaded_image_inventory"), LoadedImages);
    OutRuntimeProvenance->SetObjectField(TEXT("observed_inherited_descriptor_map"), Descriptors);
    OutRuntimeProvenance->SetArrayField(TEXT("observed_launch_argv"), ArgvValues);
    OutRuntimeProvenance->SetObjectField(TEXT("observed_process_binding"), Observed);
    OutRuntimeProvenance->SetStringField(TEXT("operational_process_instance_id"), Sha256Utf8(CanonicalizeObject(Observed)));
    OutRuntimeProvenance->SetStringField(TEXT("process_binding_raw_sha256"), Sha256Utf8(CanonicalizeObject(Observed) + TEXT("\n")));
    OutRuntimeProvenance->SetObjectField(TEXT("project_config_and_module_inventory"), Project);
    OutRuntimeProvenance->SetStringField(TEXT("proof_scenario"), Scenario);
    OutRuntimeProvenance->SetObjectField(TEXT("redacted_environment_audit"), Environment);
    return true;
}

bool FCrossDomainOccupancyCommandRouter::AcceptBinding(
    const TSharedPtr<FJsonObject>& Command,
    FString& OutReason)
{
    using namespace CrossDomainOccupancyJson;
    if (bBindingAccepted || !HasExactKeys(Command, {
        TEXT("bind_invocation_schema"), TEXT("command_sequence"), TEXT("operational_process_instance_id"),
        TEXT("process_binding"), TEXT("process_binding_raw_sha256"), TEXT("proof_scenario")
    }) || !ExactString(Command, TEXT("bind_invocation_schema"), BindSchema) ||
        !ExactString(Command, TEXT("proof_scenario"), Scenario))
    {
        OutReason = TEXT("invalid_or_duplicate_binding_command");
        return false;
    }
    int32 Sequence = -1;
    const TSharedPtr<FJsonObject>* ProcessBinding = nullptr;
    FString InstanceId;
    FString BindingDigest;
    TSharedPtr<FJsonObject> RuntimeProvenance;
    if (!ExactInteger(Command, TEXT("command_sequence"), Sequence) || Sequence != 0 ||
        !Command->TryGetObjectField(TEXT("process_binding"), ProcessBinding) || !ProcessBinding ||
        !Command->TryGetStringField(TEXT("operational_process_instance_id"), InstanceId) || !IsLowerSha256(InstanceId) ||
        !Command->TryGetStringField(TEXT("process_binding_raw_sha256"), BindingDigest) || !IsLowerSha256(BindingDigest) ||
        Sha256Utf8(CanonicalizeObject(*ProcessBinding)) != InstanceId ||
        Sha256Utf8(CanonicalizeObject(*ProcessBinding) + TEXT("\n")) != BindingDigest ||
        !VerifyObservableBinding(*ProcessBinding, RuntimeProvenance, OutReason))
    {
        if (OutReason.IsEmpty()) OutReason = TEXT("process_binding_identity_verification_failed");
        return false;
    }
    Binding.CompleteBinding = *ProcessBinding;
    Binding.OperationalProcessInstanceId = InstanceId;
    Binding.ProcessBindingRawSha256 = BindingDigest;
    (*ProcessBinding)->TryGetStringField(TEXT("domain_role"), Binding.DomainRole);
    (*ProcessBinding)->TryGetStringField(TEXT("witness_id"), Binding.WitnessId);
    (*ProcessBinding)->TryGetStringField(TEXT("harness_launch_id"), Binding.HarnessLaunchId);
    (*ProcessBinding)->TryGetStringField(TEXT("process_root_realpath"), Binding.ProcessRootRealpath);
    ExactInteger(*ProcessBinding, TEXT("pid"), Binding.Pid);
    CrossDomainOccupancyRuntime::Initialize(Binding);
    CrossDomainOccupancyRuntime::BeginCommand({0, BindSchema, Sha256Utf8(CanonicalizeObject(Command) + TEXT("\n")), TEXT("bind_0001")});
    CrossDomainOccupancyRuntime::EmitStage(TEXT("binding"), TEXT("completed"), TEXT(""), TEXT(""), {}, RuntimeProvenance);
    RuntimeProvenance->SetStringField(TEXT("operational_process_instance_id"), InstanceId);
    RuntimeProvenance->SetStringField(TEXT("process_binding_raw_sha256"), BindingDigest);
    EmitStructuredObject(RuntimeProvenance);
    Adapter = MakeUnique<FCrossDomainOccupancyProofAdapter>(World.Get(), Binding);
    Probe = MakeUnique<FCrossDomainOccupancyLiveWorldProbe>(World.Get(), Binding);
    bBindingAccepted = Adapter.IsValid() && Probe.IsValid();
    if (!bBindingAccepted)
    {
        OutReason = TEXT("phase4_non_actor_surface_creation_failed");
        return false;
    }
    EmitBindReceipt();
    return true;
}

bool FCrossDomainOccupancyCommandRouter::AcceptFaultArm(
    const TSharedPtr<FJsonObject>& Command,
    FString& OutReason)
{
    using namespace CrossDomainOccupancyJson;
    if (bFaultArmAccepted || !HasExactKeys(Command, {
        TEXT("armed_operation_id"), TEXT("case_id"), TEXT("edge"), TEXT("fault_arm_invocation_schema"),
        TEXT("fault_occurrence_id"), TEXT("operational_process_instance_id"), TEXT("proof_scenario"), TEXT("stage_id")
    }) || !ExactString(Command, TEXT("fault_arm_invocation_schema"), FaultArmSchema) ||
        !ExactString(Command, TEXT("proof_scenario"), Scenario) ||
        !ExactString(Command, TEXT("operational_process_instance_id"), *Binding.OperationalProcessInstanceId))
    {
        OutReason = TEXT("fault_arm_structure_or_binding_mismatch");
        return false;
    }
    Command->TryGetStringField(TEXT("fault_occurrence_id"), FaultPlan.FaultOccurrenceId);
    Command->TryGetStringField(TEXT("case_id"), FaultPlan.CaseId);
    Command->TryGetStringField(TEXT("stage_id"), FaultPlan.StageId);
    Command->TryGetStringField(TEXT("edge"), FaultPlan.Edge);
    Command->TryGetStringField(TEXT("armed_operation_id"), FaultPlan.ArmedOperationId);
    const bool bStage = IsMaterializationStage(FaultPlan.StageId) || IsObservationProcessStage(FaultPlan.StageId);
    const bool bEdge = FaultPlan.Edge == TEXT("before") || FaultPlan.Edge == TEXT("after");
    const bool bOperation = FaultPlan.ArmedOperationId == TEXT("launch_0001") ||
        FaultPlan.ArmedOperationId == TEXT("refresh_0001") || FaultPlan.ArmedOperationId == TEXT("refresh_0002") ||
        IsInspectionId(FaultPlan.ArmedOperationId);
    const bool bWitness = Binding.WitnessId == TEXT("fault_materialization") ||
        Binding.WitnessId == TEXT("fault_live_observation") || Binding.WitnessId == TEXT("c2_positive_Rtransit_absence") ||
        Binding.WitnessId == TEXT("c3_receipt_only_rejection") || Binding.WitnessId == TEXT("authority_adversary");
    if (!bStage || !bEdge || !bOperation || !bWitness || FaultPlan.FaultOccurrenceId.IsEmpty() || FaultPlan.CaseId.IsEmpty())
    {
        OutReason = TEXT("fault_arm_case_stage_or_witness_mismatch");
        return false;
    }
    if ((FaultPlan.CaseId == TEXT("control_C2") && (Binding.DomainRole != TEXT("domain_B") ||
        FaultPlan.StageId != TEXT("M20_spawn_configure_and_finish_target_anchor") || FaultPlan.Edge != TEXT("before") ||
        FaultPlan.ArmedOperationId != TEXT("refresh_0001"))) ||
        (FaultPlan.CaseId == TEXT("control_C3") && (Binding.DomainRole != TEXT("domain_B") ||
        FaultPlan.StageId != TEXT("M16_validate_candidate_coherence_and_cardinality") || FaultPlan.Edge != TEXT("after") ||
        FaultPlan.ArmedOperationId != TEXT("refresh_0001"))))
    {
        OutReason = TEXT("control_fault_arm_cross_product_mismatch");
        return false;
    }
    FaultPlan.bArmed = true;
    bFaultArmAccepted = true;
    return true;
}

void FCrossDomainOccupancyCommandRouter::EmitBindReceipt() const
{
    TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
    Receipt->SetStringField(TEXT("bind_receipt_schema"), TEXT("CrossDomainOccupancyBindReceipt.v1"));
    Receipt->SetStringField(TEXT("domain_role"), Binding.DomainRole);
    Receipt->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    Receipt->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
    Receipt->SetStringField(TEXT("proof_scenario"), Scenario);
    Receipt->SetStringField(TEXT("state"), TEXT("binding_accepted_once"));
    CrossDomainOccupancyJson::EmitStructuredObject(Receipt);
}

void FCrossDomainOccupancyCommandRouter::EmitFaultArmReceipt() const
{
    TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
    Receipt->SetStringField(TEXT("arm_state"), TEXT("armed_once"));
    Receipt->SetStringField(TEXT("armed_operation_id"), FaultPlan.ArmedOperationId);
    Receipt->SetStringField(TEXT("case_id"), FaultPlan.CaseId);
    Receipt->SetStringField(TEXT("edge"), FaultPlan.Edge);
    Receipt->SetStringField(TEXT("fault_occurrence_id"), FaultPlan.FaultOccurrenceId);
    Receipt->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    Receipt->SetStringField(TEXT("process_fault_arm_receipt_schema"), TEXT("CrossDomainOccupancyProcessFaultArmReceipt.v1"));
    Receipt->SetStringField(TEXT("proof_scenario"), Scenario);
    Receipt->SetStringField(TEXT("stage_id"), FaultPlan.StageId);
    CrossDomainOccupancyJson::EmitStructuredObject(Receipt);
}

void FCrossDomainOccupancyCommandRouter::HandleLine(const FString& CanonicalLine)
{
    using namespace CrossDomainOccupancyJson;
    TSharedPtr<FJsonObject> Command;
    if (!ParseCanonicalObject(CanonicalLine, Command))
    {
        bProtocolFailed = true;
        EmitFailure(TEXT("command_parse"), TEXT("noncanonical_stdin_command"));
        return;
    }
    if (!bBindingAccepted)
    {
        FString Reason;
        if (!AcceptBinding(Command, Reason))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("binding"), Reason);
        }
        return;
    }
    if (bProtocolFailed)
    {
        EmitFailure(TEXT("command_dispatch"), TEXT("command_after_protocol_failure"));
        return;
    }
    FString Schema;
    if (Command->TryGetStringField(TEXT("fault_arm_invocation_schema"), Schema) && Schema == FaultArmSchema)
    {
        FString Reason;
        if (!AcceptFaultArm(Command, Reason))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("fault_arm"), Reason);
        }
        else EmitFaultArmReceipt();
        return;
    }

    if (Command->TryGetStringField(TEXT("liveness_invocation_schema"), Schema) && Schema == LivenessSchema)
    {
        FString CaseId;
        FString ActionId;
        int32 Sequence = -1;
        if (Binding.WitnessId != TEXT("liveness_adversary") || !HasExactKeys(Command, {
            TEXT("action_id"), TEXT("case_id"), TEXT("command_sequence"), TEXT("liveness_invocation_schema"),
            TEXT("liveness_plan_raw_sha256"), TEXT("operation"), TEXT("operational_process_instance_id"), TEXT("proof_scenario")
        }) || !ExactString(Command, TEXT("proof_scenario"), Scenario) ||
            !ExactString(Command, TEXT("operation"), TEXT("execute_liveness_adversary_once")) ||
            !ExactString(Command, TEXT("operational_process_instance_id"), *Binding.OperationalProcessInstanceId) ||
            !ExactInteger(Command, TEXT("command_sequence"), Sequence) || Sequence != LastCommandSequence + 1 ||
            !Command->TryGetStringField(TEXT("case_id"), CaseId) || !Command->TryGetStringField(TEXT("action_id"), ActionId))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("liveness_adversary"), TEXT("liveness_invocation_mismatch"));
            return;
        }
        LastCommandSequence = Sequence;
        FCDOCommandContext Context {Sequence, LivenessSchema, Sha256Utf8(CanonicalLine + TEXT("\n")), FString::Printf(TEXT("liveness_%s"), *CaseId)};
        CrossDomainOccupancyRuntime::BeginCommand(Context);
        CrossDomainOccupancyRuntime::EmitStage(FString::Printf(TEXT("liveness_%s_%s"), *CaseId, *ActionId), TEXT("entered"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash());
        TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
        Receipt->SetStringField(TEXT("action_id"), ActionId);
        Receipt->SetStringField(TEXT("arm_state"), TEXT("armed_once_before_action"));
        Receipt->SetStringField(TEXT("case_id"), CaseId);
        Receipt->SetStringField(TEXT("liveness_arm_receipt_schema"), TEXT("CrossDomainOccupancyLivenessAdversaryArmReceipt.v1"));
        Receipt->SetStringField(TEXT("liveness_invocation_raw_sha256"), Context.CommandRawSha256);
        Receipt->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
        Receipt->SetStringField(TEXT("proof_scenario"), Scenario);
        EmitStructuredObject(Receipt);
        if (CaseId == TEXT("LV03") && ActionId == TEXT("emit_changed_start_report"))
        {
            const TSharedPtr<FJsonObject>* Start = nullptr;
            Binding.CompleteBinding->TryGetObjectField(TEXT("macos_process_start"), Start);
            double Seconds = 0;
            double Microseconds = 0;
            (*Start)->TryGetNumberField(TEXT("seconds"), Seconds);
            (*Start)->TryGetNumberField(TEXT("microseconds"), Microseconds);
            TSharedPtr<FJsonObject> ReportedStart = MakeShared<FJsonObject>();
            ReportedStart->SetNumberField(TEXT("microseconds"), Microseconds);
            ReportedStart->SetNumberField(TEXT("seconds"), Seconds + 1);
            TSharedPtr<FJsonObject> Report = MakeShared<FJsonObject>();
            Report->SetStringField(TEXT("action_id"), ActionId);
            Report->SetStringField(TEXT("case_id"), CaseId);
            Report->SetStringField(TEXT("checkpoint_id"), TEXT("L2"));
            Report->SetNumberField(TEXT("command_sequence"), Sequence);
            Report->SetStringField(TEXT("domain_role"), Binding.DomainRole);
            Report->SetStringField(TEXT("liveness_adversarial_report_schema"), TEXT("CrossDomainOccupancyLivenessAdversarialReport.v1"));
            Report->SetStringField(TEXT("occurrence_id"), Binding.HarnessLaunchId);
            Report->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
            Report->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
            Report->SetStringField(TEXT("proof_scenario"), Scenario);
            Report->SetNumberField(TEXT("report_sequence"), 0);
            Report->SetNumberField(TEXT("reported_pid"), Binding.Pid);
            Report->SetObjectField(TEXT("reported_macos_process_start"), ReportedStart);
            Report->SetStringField(TEXT("report_source"), TEXT("adversarial_child_report"));
            EmitStructuredObject(Report);
            CrossDomainOccupancyRuntime::EmitStage(FString::Printf(TEXT("liveness_%s_%s"), *CaseId, *ActionId), TEXT("completed"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash(), {}, Report);
        }
        else if (CaseId == TEXT("LV04") && ActionId == TEXT("close_control_read_endpoint"))
        {
            close(STDIN_FILENO);
            CrossDomainOccupancyRuntime::EmitStage(TEXT("liveness_LV04_close_control_read_endpoint"), TEXT("completed"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash());
        }
        else if (CaseId == TEXT("LV05") && ActionId == TEXT("close_structured_output_write_endpoint"))
        {
            fflush(stdout);
            close(STDOUT_FILENO);
        }
        else
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("liveness_adversary"), TEXT("liveness_case_action_cross_product_mismatch"));
        }
        return;
    }

    int32 Sequence = -1;
    if (!ExactInteger(Command, TEXT("command_sequence"), Sequence) || Sequence != LastCommandSequence + 1)
    {
        bProtocolFailed = true;
        EmitFailure(TEXT("command_sequence"), TEXT("missing_duplicate_or_reordered_command"));
        return;
    }

    if (Command->TryGetStringField(TEXT("materialize_invocation_schema"), Schema) && Schema == MaterializeSchema)
    {
        FString Operation;
        FString OperationId;
        FString RelativeRoot;
        if (bTerminalLocalInvalid || !HasExactKeys(Command, {
            TEXT("command_sequence"), TEXT("materialize_invocation_schema"), TEXT("operation"),
            TEXT("operation_id"), TEXT("proof_scenario"), TEXT("relative_bundle_root")
        }) || !ExactString(Command, TEXT("proof_scenario"), Scenario) ||
            !Command->TryGetStringField(TEXT("operation"), Operation) ||
            !Command->TryGetStringField(TEXT("operation_id"), OperationId) ||
            !Command->TryGetStringField(TEXT("relative_bundle_root"), RelativeRoot) ||
            !((OperationId == TEXT("launch_0001") && Operation == TEXT("materialize_initial") && LastCommandSequence == 0) ||
              (OperationId == TEXT("refresh_0001") && Operation == TEXT("refresh_once") && Adapter->GetRepresentedCanonicalHash() == TEXT("b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8")) ||
              (OperationId == TEXT("refresh_0002") && Operation == TEXT("refresh_once") && Adapter->GetRepresentedCanonicalHash() == TEXT("2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19"))))
        {
            bProtocolFailed = true;
            EmitFailure(TEXT("M01_receive_and_parse_command"), TEXT("materialize_command_cross_product_mismatch"));
            return;
        }
        LastCommandSequence = Sequence;
        const FString RawDigest = Sha256Utf8(CanonicalLine + TEXT("\n"));
        CrossDomainOccupancyRuntime::BeginCommand({Sequence, MaterializeSchema, RawDigest, OperationId});
        CrossDomainOccupancyRuntime::EmitStage(TEXT("M01_receive_and_parse_command"), TEXT("entered"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash());
        FString Reason;
        if (CrossDomainOccupancyRuntime::InjectAt(&FaultPlan, TEXT("M01_receive_and_parse_command"), TEXT("before"), Reason))
        {
            bTerminalLocalInvalid = true;
            EmitFailure(TEXT("M01_receive_and_parse_command"), Reason);
            return;
        }
        CrossDomainOccupancyRuntime::EmitStage(TEXT("M01_receive_and_parse_command"), TEXT("completed"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash());
        if (CrossDomainOccupancyRuntime::InjectAt(&FaultPlan, TEXT("M01_receive_and_parse_command"), TEXT("after"), Reason))
        {
            bTerminalLocalInvalid = true;
            EmitFailure(TEXT("M01_receive_and_parse_command"), Reason);
            return;
        }
        TSharedPtr<FJsonObject> Receipt;
        if (!Adapter->MaterializeOnce(OperationId, RelativeRoot, RawDigest, &FaultPlan, Receipt, Reason))
        {
            bTerminalLocalInvalid = true;
            if (Receipt.IsValid()) EmitStructuredObject(Receipt);
            EmitFailure(FaultPlan.bInjected ? FaultPlan.StageId : TEXT("materialization"), Reason);
            return;
        }
        CrossDomainOccupancyRuntime::EmitStage(TEXT("M23_router_forward_receipt"), TEXT("entered"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash());
        if (CrossDomainOccupancyRuntime::InjectAt(&FaultPlan, TEXT("M23_router_forward_receipt"), TEXT("before"), Reason))
        {
            bTerminalLocalInvalid = true;
            Adapter->MarkInvalid();
            EmitFailure(TEXT("M23_router_forward_receipt"), Reason);
            return;
        }
        EmitStructuredObject(Receipt);
        CrossDomainOccupancyRuntime::EmitStage(TEXT("M23_router_forward_receipt"), TEXT("completed"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash(), {}, Receipt);
        if (CrossDomainOccupancyRuntime::InjectAt(&FaultPlan, TEXT("M23_router_forward_receipt"), TEXT("after"), Reason))
        {
            bTerminalLocalInvalid = true;
            Adapter->MarkInvalid();
            EmitFailure(TEXT("M23_router_forward_receipt"), Reason);
        }
        return;
    }

    if (Command->TryGetStringField(TEXT("inspection_invocation_schema"), Schema) && Schema == InspectionSchema)
    {
        FString InspectionId;
        const bool bSpecialAfterInvalid = bTerminalLocalInvalid &&
            ((Binding.WitnessId == TEXT("c2_positive_Rtransit_absence") &&
              Command->TryGetStringField(TEXT("inspection_id"), InspectionId) && InspectionId == TEXT("inspection_c2_rejection_0001")) ||
             (Binding.WitnessId == TEXT("c3_receipt_only_rejection") &&
              Command->TryGetStringField(TEXT("inspection_id"), InspectionId) && InspectionId == TEXT("inspection_c3_rejection_0001")) ||
             (Binding.WitnessId.StartsWith(TEXT("af_Rtransit_")) &&
              Command->TryGetStringField(TEXT("inspection_id"), InspectionId) && InspectionId == TEXT("inspection_0005")) ||
             (Binding.WitnessId.StartsWith(TEXT("af_Rfinal_")) &&
              Command->TryGetStringField(TEXT("inspection_id"), InspectionId) && InspectionId == TEXT("inspection_0009")));
        if ((!Adapter->GetPublicationGeneration().IsEmpty() || bSpecialAfterInvalid) && HasExactKeys(Command, {
            TEXT("command_sequence"), TEXT("inspection_id"), TEXT("inspection_invocation_schema"),
            TEXT("operation"), TEXT("proof_scenario")
        }) && ExactString(Command, TEXT("proof_scenario"), Scenario) &&
            ExactString(Command, TEXT("operation"), TEXT("inspect_published_occupancy_once")) &&
            Command->TryGetStringField(TEXT("inspection_id"), InspectionId) && IsInspectionId(InspectionId))
        {
            LastCommandSequence = Sequence;
            const FString RawDigest = Sha256Utf8(CanonicalLine + TEXT("\n"));
            CrossDomainOccupancyRuntime::BeginCommand({Sequence, InspectionSchema, RawDigest, InspectionId});
            CrossDomainOccupancyRuntime::EmitStage(TEXT("O01_receive_and_parse_inspection_command"), TEXT("entered"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash());
            FString Reason;
            if (CrossDomainOccupancyRuntime::InjectAt(&FaultPlan, TEXT("O01_receive_and_parse_inspection_command"), TEXT("before"), Reason))
            {
                bTerminalLocalInvalid = true;
                Adapter->MarkInvalid();
                EmitFailure(TEXT("O01_receive_and_parse_inspection_command"), Reason);
                return;
            }
            CrossDomainOccupancyRuntime::EmitStage(TEXT("O01_receive_and_parse_inspection_command"), TEXT("completed"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash());
            if (CrossDomainOccupancyRuntime::InjectAt(&FaultPlan, TEXT("O01_receive_and_parse_inspection_command"), TEXT("after"), Reason))
            {
                bTerminalLocalInvalid = true;
                Adapter->MarkInvalid();
                EmitFailure(TEXT("O01_receive_and_parse_inspection_command"), Reason);
                return;
            }
            TSharedPtr<FJsonObject> Observation;
            if (!Probe->InspectOnce(InspectionId, &FaultPlan, Observation, Reason))
            {
                bTerminalLocalInvalid = true;
                Adapter->MarkInvalid();
                EmitFailure(FaultPlan.bInjected ? FaultPlan.StageId : TEXT("inspection"), Reason);
                return;
            }
            CrossDomainOccupancyRuntime::EmitStage(TEXT("O10_router_forward_live_observation"), TEXT("entered"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash());
            if (CrossDomainOccupancyRuntime::InjectAt(&FaultPlan, TEXT("O10_router_forward_live_observation"), TEXT("before"), Reason))
            {
                bTerminalLocalInvalid = true;
                Adapter->MarkInvalid();
                EmitFailure(TEXT("O10_router_forward_live_observation"), Reason);
                return;
            }
            EmitStructuredObject(Observation);
            CrossDomainOccupancyRuntime::EmitStage(TEXT("O10_router_forward_live_observation"), TEXT("completed"), Adapter->GetPublicationGeneration(), Adapter->GetRepresentedCanonicalHash(), {}, Observation);
            if (CrossDomainOccupancyRuntime::InjectAt(&FaultPlan, TEXT("O10_router_forward_live_observation"), TEXT("after"), Reason))
            {
                bTerminalLocalInvalid = true;
                Adapter->MarkInvalid();
                EmitFailure(TEXT("O10_router_forward_live_observation"), Reason);
            }
            return;
        }
    }
    bProtocolFailed = true;
    EmitFailure(TEXT("command_dispatch"), TEXT("unknown_or_out_of_order_command_schema"));
}

void FCrossDomainOccupancyCommandRouter::EmitFailure(
    const FString& StageId,
    const FString& ReasonCode) const
{
    TSharedPtr<FJsonObject> Failure = MakeShared<FJsonObject>();
    Failure->SetStringField(TEXT("diagnostic_schema"), TEXT("CrossDomainOccupancyFailure.v1"));
    Failure->SetStringField(TEXT("domain_role"), Binding.DomainRole.IsEmpty() ? TEXT("unbound") : Binding.DomainRole);
    Failure->SetBoolField(TEXT("fault_injected"), FaultPlan.bInjected);
    Failure->SetStringField(TEXT("local_publication_state"), Adapter.IsValid() ? Adapter->GetPublicationState() : TEXT("none"));
    Failure->SetStringField(TEXT("operational_process_instance_id"), Binding.OperationalProcessInstanceId);
    Failure->SetStringField(TEXT("process_binding_raw_sha256"), Binding.ProcessBindingRawSha256);
    Failure->SetStringField(TEXT("proof_scenario"), Scenario);
    Failure->SetStringField(TEXT("publication_generation"), Adapter.IsValid() ? Adapter->GetPublicationGeneration() : TEXT(""));
    Failure->SetStringField(TEXT("reason_code"), ReasonCode.IsEmpty() ? TEXT("unspecified_phase4_failure") : ReasonCode);
    Failure->SetStringField(TEXT("represented_canonical_hash"), Adapter.IsValid() ? Adapter->GetRepresentedCanonicalHash() : TEXT(""));
    Failure->SetStringField(TEXT("stage_id"), StageId);
    CrossDomainOccupancyJson::EmitStructuredObject(Failure);
}
