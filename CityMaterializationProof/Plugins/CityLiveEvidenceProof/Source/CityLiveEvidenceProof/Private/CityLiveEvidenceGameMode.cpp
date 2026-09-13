#include "CityLiveEvidenceGameMode.h"
#include "CityLiveEvidenceActors.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Engine.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "Misc/CommandLine.h"
#include "Misc/Paths.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Modules/ModuleManager.h"
#include "UObject/Package.h"
#include <atomic>
#include <cerrno>
#include <crt_externs.h>
#include <fcntl.h>
#include <libproc.h>
#include <mach/mach.h>
#include <mach-o/dyld.h>
#include <mach-o/dyld_images.h>
#include <mach-o/loader.h>
#include <openssl/sha.h>
#include <poll.h>
#include <pwd.h>
#include <sys/file.h>
#include <sys/proc_info.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <unistd.h>

class FLCERInputThread final : public FRunnable
{
public:
    explicit FLCERInputThread(ACityLiveEvidenceGameMode* InOwner) : Owner(InOwner) {}
    virtual uint32 Run() override
    {
        TArray<ANSICHAR> Pending;
        while (!bStopRequested.load())
        {
            pollfd Poll = {STDIN_FILENO, POLLIN, 0};
            const int Ready = poll(&Poll, 1, 100);
            if (Ready < 0 && errno == EINTR) continue;
            if (Ready == 0) continue;
            if (Ready < 0) { Owner->EnqueueInput(FString()); return 2; }
            ANSICHAR Buffer[4096];
            const ssize_t Count = read(STDIN_FILENO, Buffer, sizeof(Buffer));
            if (Count < 0 && errno == EINTR) continue;
            if (Count <= 0) { Owner->EnqueueInput(FString()); return 0; }
            for (ssize_t Index = 0; Index < Count; ++Index)
            {
                Pending.Add(Buffer[Index]);
                if (Buffer[Index] == '\n')
                {
                    FUTF8ToTCHAR Converter(Pending.GetData(), Pending.Num());
                    const FString Line(Converter.Length(), Converter.Get());
                    FTCHARToUTF8 RoundTrip(*Line, Line.Len());
                    if (RoundTrip.Length() != Pending.Num() ||
                        FMemory::Memcmp(RoundTrip.Get(), Pending.GetData(), Pending.Num()) != 0)
                    {
                        // Decoder replacement must never normalize unaccepted
                        // wire bytes into a different command.
                        Owner->EnqueueInput(FString());
                        return 2;
                    }
                    Owner->EnqueueInput(Line);
                    Pending.Reset(0);
                }
            }
        }
        return 0;
    }
    virtual void Stop() override { bStopRequested.store(true); }

private:
    ACityLiveEvidenceGameMode* Owner;
    std::atomic<bool> bStopRequested{false};
};

namespace
{
using FObject = TSharedPtr<FJsonObject>;
using FValue = TSharedPtr<FJsonValue>;

FObject PlatformFileIdentity(const FString& Path)
{
    FTCHARToUTF8 InputPath(*Path);
    char Resolved[PATH_MAX];
    if (!realpath(InputPath.Get(), Resolved)) return nullptr;
    const int Descriptor = open(Resolved, O_RDONLY | O_CLOEXEC);
    if (Descriptor < 0) return nullptr;
    struct stat Before{}, After{};
    if (fstat(Descriptor, &Before) != 0 || !S_ISREG(Before.st_mode)) { close(Descriptor); return nullptr; }
    SHA256_CTX Context;
    SHA256_Init(&Context);
    uint8 Buffer[65536];
    off_t Count = 0;
    bool bComplete = true;
    while (true)
    {
        const ssize_t Read = read(Descriptor, Buffer, sizeof(Buffer));
        if (Read < 0 && errno == EINTR) continue;
        if (Read < 0) { bComplete = false; break; }
        if (Read == 0) break;
        Count += Read;
        SHA256_Update(&Context, Buffer, Read);
    }
    const bool bStable = fstat(Descriptor, &After) == 0 && Before.st_dev == After.st_dev && Before.st_ino == After.st_ino &&
        Before.st_size == After.st_size && Before.st_mtimespec.tv_sec == After.st_mtimespec.tv_sec &&
        Before.st_mtimespec.tv_nsec == After.st_mtimespec.tv_nsec && Count == Before.st_size;
    close(Descriptor);
    if (!bComplete || !bStable) return nullptr;
    uint8 Hash[SHA256_DIGEST_LENGTH];
    SHA256_Final(Hash, &Context);
    FString Hex;
    for (uint8 Byte : Hash) Hex += FString::Printf(TEXT("%02x"), Byte);
    const auto Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("realpath"), UTF8_TO_TCHAR(Resolved));
    Result->SetStringField(TEXT("sha256"), Hex);
    Result->SetNumberField(TEXT("size_bytes"), static_cast<double>(Count));
    return Result;
}

bool PlatformLaunchInputs(TArray<FValue>& Arguments, FObject& Environment)
{
    int SizeQuery[2] = {CTL_KERN, KERN_ARGMAX};
    int Maximum = 0;
    size_t Size = sizeof(Maximum);
    if (sysctl(SizeQuery, 2, &Maximum, &Size, nullptr, 0) != 0 || Maximum <= 0) return false;
    TArray<char> Bytes;
    Bytes.SetNumUninitialized(Maximum, EAllowShrinking::Yes);
    Size = Bytes.Num();
    int Query[3] = {CTL_KERN, KERN_PROCARGS2, getpid()};
    if (sysctl(Query, 3, Bytes.GetData(), &Size, nullptr, 0) != 0 || Size <= sizeof(int)) return false;
    int Count = 0;
    FMemory::Memcpy(&Count, Bytes.GetData(), sizeof(Count));
    if (Count <= 0) return false;
    size_t Offset = sizeof(int);
    const auto ReadString = [&Bytes, &Offset, Size](FString& Result) -> bool
    {
        const size_t Begin = Offset;
        while (Offset < Size && Bytes[Offset] != '\0') ++Offset;
        if (Offset >= Size) return false;
        FUTF8ToTCHAR Text(Bytes.GetData() + Begin, Offset - Begin);
        Result = FString(Text.Length(), Text.Get());
        ++Offset;
        return true;
    };
    FString Executable;
    if (!ReadString(Executable)) return false;
    while (Offset < Size && Bytes[Offset] == '\0') ++Offset;
    for (int Index = 0; Index < Count; ++Index)
    {
        FString Argument;
        if (!ReadString(Argument) || Argument.IsEmpty()) return false;
        Arguments.Add(MakeShared<FJsonValueString>(Argument));
    }
    // The child can inspect its real envp vector directly. KERN_PROCARGS2
    // also contains Apple's bootstrap strings and has no reliable double-NUL
    // boundary after an already-aligned environment string area.
    char** const Env = *_NSGetEnviron();
    if (!Env) return false;
    Environment = MakeShared<FJsonObject>();
    for (int Index = 0; Env[Index] != nullptr; ++Index)
    {
        if (Index >= 7) return false;
        const FString Entry = UTF8_TO_TCHAR(Env[Index]);
        FString Name, Value;
        if (!Entry.Split(TEXT("="), &Name, &Value) || Name.IsEmpty() || Environment->HasField(Name)) return false;
        Environment->SetStringField(Name, Value);
    }
    if (*_NSGetEnviron() != Env) return false;
    return CityLCER::Keys(Environment, {TEXT("HOME"), TEXT("TMPDIR"), TEXT("USER"), TEXT("LOGNAME"), TEXT("PATH"), TEXT("LANG"), TEXT("LC_ALL")});
}

bool PlatformProofDescriptors(TArray<FValue>& Rows)
{
    for (int Fd = 0; Fd < 3; ++Fd)
    {
        struct pipe_fdinfo Info{};
        if (proc_pidfdinfo(getpid(), Fd, PROC_PIDFDPIPEINFO, &Info, sizeof(Info)) != sizeof(Info) ||
            Info.pipeinfo.pipe_handle == 0 || Info.pipeinfo.pipe_peerhandle == 0) return false;
        const bool bRead = (Info.pfi.fi_openflags & FREAD) != 0;
        const bool bWrite = (Info.pfi.fi_openflags & FWRITE) != 0;
        if ((Fd == 0 && (!bRead || bWrite)) || (Fd != 0 && (bRead || !bWrite))) return false;
        const auto Row = MakeShared<FJsonObject>();
        Row->SetNumberField(TEXT("pid"), getpid());
        Row->SetNumberField(TEXT("fd"), Fd);
        Row->SetStringField(TEXT("kind"), TEXT("pipe"));
        Row->SetStringField(TEXT("kernel_id"), FString::Printf(TEXT("%016llx"), Info.pipeinfo.pipe_handle));
        Row->SetStringField(TEXT("peer_kernel_id"), FString::Printf(TEXT("%016llx"), Info.pipeinfo.pipe_peerhandle));
        Row->SetStringField(TEXT("access"), bRead ? TEXT("read") : TEXT("write"));
        Row->SetField(TEXT("path"), MakeShared<FJsonValueNull>());
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    return true;
}

FString PlatformUuid(const uint8* Bytes)
{
    FString Result;
    for (int Index = 0; Index < 16; ++Index)
    {
        if (Index == 4 || Index == 6 || Index == 8 || Index == 10) Result += TEXT("-");
        Result += FString::Printf(TEXT("%02x"), Bytes[Index]);
    }
    return Result;
}

bool PlatformImages(TArray<FValue>& Rows, FObject& ProofModule)
{
    task_dyld_info_data_t Task{};
    mach_msg_type_number_t TaskCount = TASK_DYLD_INFO_COUNT;
    if (task_info(mach_task_self(), TASK_DYLD_INFO, reinterpret_cast<task_info_t>(&Task), &TaskCount) != KERN_SUCCESS ||
        Task.all_image_info_addr == 0 || Task.all_image_info_size < sizeof(dyld_all_image_infos)) return false;
    const auto* Info = reinterpret_cast<const dyld_all_image_infos*>(Task.all_image_info_addr);
    if (Info->version < 15 || Info->processDetachedFromSharedRegion || Info->sharedCacheBaseAddress == 0) return false;
    const uint64 Stamp = Info->infoArrayChangeTimestamp;
    uint8 CacheUuid[16];
    FMemory::Memcpy(CacheUuid, Info->sharedCacheUUID, 16);
    FObject Cache(nullptr);
    // Match the kernel-observed cache UUID to actual cache bytes, not to a
    // selected filename alone. UUID is at byte 88 in Apple's cache header:
    // https://github.com/apple-oss-distributions/dyld/blob/main/include/mach-o/dyld_cache_format.h
    for (const TCHAR* Directory : {TEXT("/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld"),
                                   TEXT("/System/Library/dyld")})
    {
        for (const TCHAR* Name : {TEXT("dyld_shared_cache_arm64e"), TEXT("dyld_shared_cache_x86_64")})
        {
            const FString Path = FString(Directory) + TEXT("/") + Name;
            FTCHARToUTF8 Utf8(*Path);
            const int Fd = open(Utf8.Get(), O_RDONLY | O_CLOEXEC);
            if (Fd < 0) continue;
            uint8 Header[104];
            const ssize_t Count = pread(Fd, Header, sizeof(Header), 0);
            close(Fd);
            if (Count != sizeof(Header) || FMemory::Memcmp(Header, "dyld_v1", 7) != 0 ||
                FMemory::Memcmp(Header + 88, CacheUuid, 16) != 0) continue;
            Cache = PlatformFileIdentity(Path);
            if (!Cache.IsValid()) return false;
            break;
        }
        if (Cache.IsValid()) break;
    }
    if (!Cache.IsValid()) return false;
    const auto ModuleFile = PlatformFileIdentity(FPaths::ConvertRelativePathToFull(
        FModuleManager::Get().GetModuleFilename(TEXT("CityLiveEvidenceProof"))));
    if (!ModuleFile.IsValid()) return false;
    const uint32 ImageCount = _dyld_image_count();
    TArray<FObject> Images;
    TArray<FString> ImagePaths;
    // dyld itself is executable code visible in vmmap, but is deliberately
    // omitted from _dyld_image_count(). Read its actual loader header/path too.
    if (!Info->dyldImageLoadAddress || !Info->dyldPath) return false;
    for (uint32 Index = 0; Index <= ImageCount; ++Index)
    {
        const mach_header* Header = Index == ImageCount ? Info->dyldImageLoadAddress : _dyld_get_image_header(Index);
        const char* ImageName = Index == ImageCount ? Info->dyldPath : _dyld_get_image_name(Index);
        if (!Header || !ImageName || Header->magic != MH_MAGIC_64) return false;
        const auto* Header64 = reinterpret_cast<const mach_header_64*>(Header);
        const uint8* Commands = reinterpret_cast<const uint8*>(Header64 + 1);
        uint32 Offset = 0;
        FString Uuid;
        for (uint32 CommandIndex = 0; CommandIndex < Header64->ncmds; ++CommandIndex)
        {
            if (Offset > Header64->sizeofcmds || Header64->sizeofcmds - Offset < sizeof(load_command)) return false;
            const auto* Command = reinterpret_cast<const load_command*>(Commands + Offset);
            if (Command->cmdsize < sizeof(load_command) || Command->cmdsize > Header64->sizeofcmds - Offset) return false;
            if (Command->cmd == LC_UUID)
            {
                if (!Uuid.IsEmpty() || Command->cmdsize != sizeof(uuid_command)) return false;
                Uuid = PlatformUuid(reinterpret_cast<const uuid_command*>(Command)->uuid);
            }
            Offset += Command->cmdsize;
        }
        if (Offset != Header64->sizeofcmds || Uuid.IsEmpty()) return false;
        FString Architecture;
        if (Header->cputype == CPU_TYPE_ARM64)
            Architecture = (Header->cpusubtype & ~CPU_SUBTYPE_MASK) == CPU_SUBTYPE_ARM64E ? TEXT("arm64e") : TEXT("arm64");
        else if (Header->cputype == CPU_TYPE_X86_64) Architecture = TEXT("x86_64");
        else return false;
        const bool bCached = _dyld_shared_cache_contains_path(ImageName);
        const FString ImagePath = UTF8_TO_TCHAR(ImageName);
        const auto File = bCached ? Cache : PlatformFileIdentity(ImagePath);
        if (!File.IsValid()) return false;
        const FString RealPath = bCached ? ImagePath : File->GetStringField(TEXT("realpath"));
        if (CityLCER::Contains(ImagePaths, RealPath)) return false;
        ImagePaths.Add(RealPath);
        const auto Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("realpath"), RealPath);
        Row->SetStringField(TEXT("sha256"), File->GetStringField(TEXT("sha256")));
        Row->SetStringField(TEXT("macho_uuid"), Uuid);
        Row->SetStringField(TEXT("architecture"), Architecture);
        Row->SetStringField(TEXT("source"), bCached ? TEXT("dyld_shared_cache") : TEXT("dyld"));
        Images.Add(Row);
        if (CityLCER::Exact(RealPath, ModuleFile->GetStringField(TEXT("realpath"))))
        {
            if (ProofModule.IsValid() || bCached) return false;
            ProofModule = Row;
        }
    }
    if (!ProofModule.IsValid() || _dyld_image_count() != ImageCount || Info->infoArrayChangeTimestamp != Stamp ||
        FMemory::Memcmp(Info->sharedCacheUUID, CacheUuid, 16) != 0) return false;
    Images.Sort([](const FObject& Left, const FObject& Right)
        { return CityLCER::Less(Left->GetStringField(TEXT("realpath")), Right->GetStringField(TEXT("realpath"))); });
    for (const auto& Image : Images) Rows.Add(MakeShared<FJsonValueObject>(Image));
    return true;
}

bool PlatformConfigAndPlugins(TArray<FValue>& ConfigRows, TArray<FValue>& PluginRows)
{
    if (!GConfig) return false;
    TArray<FString> ConfigPaths;
    const TArray<FString> Names = GConfig->GetFilenames();
    for (const FString& Name : Names)
    {
        const FConfigBranch* Branch = GConfig->FindBranchWithNoReload(NAME_None, Name);
        if (!Branch || Branch->bIsSafeUnloaded || !Branch->CommandLineOverrides.IsEmpty()) return false;
        // Read source filenames only. No configuration value enters proof logic.
        for (const auto& Layer : Branch->Hierarchy)
        {
            const FString Path(Layer.Value);
            if (FPaths::FileExists(Path)) CityLCER::AddUnique(ConfigPaths, FPaths::ConvertRelativePathToFull(Path));
        }
        for (const auto& Layer : Branch->StaticLayers)
        {
            const FString Path = Layer.Value.Filename;
            if (!Path.IsEmpty() && FPaths::FileExists(Path)) CityLCER::AddUnique(ConfigPaths, FPaths::ConvertRelativePathToFull(Path));
        }
        for (const FConfigCommandStream* Layer : Branch->DynamicLayers)
        {
            if (!Layer || Layer->Filename.IsEmpty() || !FPaths::FileExists(Layer->Filename)) return false;
            CityLCER::AddUnique(ConfigPaths, FPaths::ConvertRelativePathToFull(Layer->Filename));
        }
        if (!Branch->SavedLayer.IsEmpty())
        {
            if (Branch->SavedLayer.Filename.IsEmpty() || !FPaths::FileExists(Branch->SavedLayer.Filename)) return false;
            CityLCER::AddUnique(ConfigPaths, FPaths::ConvertRelativePathToFull(Branch->SavedLayer.Filename));
        }
    }
    TArray<FString> SortedConfigs = ConfigPaths;
    SortedConfigs.Sort(CityLCER::Less);
    for (const FString& Path : SortedConfigs)
    {
        const auto Row = PlatformFileIdentity(Path);
        if (!Row.IsValid()) return false;
        ConfigRows.Add(MakeShared<FJsonValueObject>(Row));
    }
    TArray<FString> PluginPaths;
    for (const TSharedRef<IPlugin>& Plugin : IPluginManager::Get().GetEnabledPlugins())
        PluginPaths.Add(FPaths::ConvertRelativePathToFull(Plugin->GetDescriptorFileName()));
    PluginPaths.Sort(CityLCER::Less);
    for (const FString& Path : PluginPaths)
    {
        const auto Row = PlatformFileIdentity(Path);
        if (!Row.IsValid()) return false;
        PluginRows.Add(MakeShared<FJsonValueObject>(Row));
    }
    return !ConfigRows.IsEmpty() && !PluginRows.IsEmpty();
}

FValue StringOrNull(const FString& Value)
{
    if (Value.IsEmpty()) return MakeShared<FJsonValueNull>();
    return MakeShared<FJsonValueString>(Value);
}

FString WorldTypeName(EWorldType::Type Type)
{
    switch (Type)
    {
    case EWorldType::None: return TEXT("None");
    case EWorldType::Game: return TEXT("Game");
    case EWorldType::Editor: return TEXT("Editor");
    case EWorldType::PIE: return TEXT("PIE");
    case EWorldType::EditorPreview: return TEXT("EditorPreview");
    case EWorldType::GamePreview: return TEXT("GamePreview");
    case EWorldType::GameRPC: return TEXT("GameRPC");
    case EWorldType::Inactive: return TEXT("Inactive");
    default: return FString();
    }
}

// This collector receives no expected projection, receipt or semantic selector.
// It retains complete invalid worlds so terminal failures remain observable.
bool CollectWorlds(TArray<FValue>& Worlds, TArray<FValue>& Controllers, TArray<FObject>& Relevant, int32& PawnCount)
{
    if (!IsInGameThread() || !GEngine) return false;
    PawnCount = 0;
    TArray<const FWorldContext*> Contexts;
    TArray<UWorld*> ContextWorlds;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        Contexts.Add(&Context);
        ContextWorlds.Add(Context.World());
    }
    TArray<FString> WorldPaths;
    TArray<FString> ActorIds;
    for (int32 ContextIndex = 0; ContextIndex < Contexts.Num(); ++ContextIndex)
    {
        UWorld* World = ContextWorlds[ContextIndex];
        if (!World) return false;
        const FString WorldPath = World->GetPathName();
        if (CityLCER::Contains(WorldPaths, WorldPath)) return false;
        WorldPaths.Add(WorldPath);
        const FString Type = WorldTypeName(World->WorldType);
        if (Type.IsEmpty() || Contexts[ContextIndex]->WorldType != World->WorldType) return false;
        TArray<ULevel*> NativeLevels;
        for (ULevel* Level : World->GetLevels()) NativeLevels.Add(Level);
        TArray<ULevel*> Levels = NativeLevels;
        for (ULevel* Level : Levels) if (!Level) return false;
        Levels.Sort([](const ULevel& Left, const ULevel& Right) { return CityLCER::Less(Left.GetPathName(), Right.GetPathName()); });
        TArray<TArray<TObjectPtr<AActor>>> Arrays;
        TArray<FString> LevelPaths;
        for (ULevel* Level : Levels)
        {
            Arrays.Add(Level->Actors);
            LevelPaths.Add(Level->GetPathName());
        }
        TArray<FValue> Visited;
        TArray<FValue> Nulls;
        TArray<FObject> Actors;
        int32 Slot = 0;
        for (const auto& Array : Arrays)
        {
            for (AActor* Actor : Array)
            {
                Visited.Add(MakeShared<FJsonValueNumber>(Slot));
                if (!Actor)
                {
                    Nulls.Add(MakeShared<FJsonValueNumber>(Slot++));
                    continue;
                }
                ++Slot;
                if (Actor->GetWorld() != World) return false;
                const FString ActorPath = Actor->GetPathName();
                const FString Id = WorldPath + TEXT("|") + ActorPath;
                if (CityLCER::Contains(ActorIds, Id)) return false;
                ActorIds.Add(Id);
                const auto Row = MakeShared<FJsonObject>();
                Row->SetStringField(TEXT("actor_id"), Id);
                Row->SetStringField(TEXT("actor_path"), ActorPath);
                Row->SetStringField(TEXT("world_path"), WorldPath);
                Row->SetStringField(TEXT("class_path"), Actor->GetClass()->GetPathName());
                Row->SetBoolField(TEXT("pending_kill"), Actor->IsActorBeingDestroyed() || !IsValid(Actor));
                Row->SetNumberField(TEXT("auto_receive_input"), static_cast<int32>(Actor->AutoReceiveInput));
                const ACityLiveEvidenceActor* Proof = Cast<ACityLiveEvidenceActor>(Actor);
                Row->SetField(TEXT("role"), Proof ? StringOrNull(Proof->GetEvidenceRole()) : MakeShared<FJsonValueNull>());
                Row->SetField(TEXT("domain"), Proof ? StringOrNull(Proof->GetEvidenceDomain()) : MakeShared<FJsonValueNull>());
                Row->SetField(TEXT("record_raw_sha256"), Proof ? StringOrNull(Proof->GetRecordRawSha256()) : MakeShared<FJsonValueNull>());
                Row->SetField(TEXT("allocation_owner"), Proof ? StringOrNull(Proof->GetAllocationOwner()) : MakeShared<FJsonValueNull>());
                if (Proof && Proof->GetEvidenceGeneration() >= 0)
                    Row->SetNumberField(TEXT("generation"), Proof->GetEvidenceGeneration());
                else Row->SetField(TEXT("generation"), MakeShared<FJsonValueNull>());
                Actors.Add(Row);
                if (Cast<APawn>(Actor)) ++PawnCount;
                if (Proof || CityLCER::Exact(Actor->GetClass()->GetOutermost()->GetName(), TEXT("/Script/CityMaterializationProof")))
                    Relevant.Add(Row);
                if (const AController* Controller = Cast<AController>(Actor))
                {
                    const auto ControllerRow = MakeShared<FJsonObject>();
                    ControllerRow->SetStringField(TEXT("actor_path"), ActorPath);
                    ControllerRow->SetStringField(TEXT("class_path"), Actor->GetClass()->GetPathName());
                    ControllerRow->SetField(TEXT("pawn_path"), StringOrNull(Controller->GetPawn()
                        ? Controller->GetPawn()->GetPathName() : FString()));
                    Controllers.Add(MakeShared<FJsonValueObject>(ControllerRow));
                }
            }
        }
        // Recheck the exact context, level order and array pointers after reads.
        if (World->GetLevels().Num() != NativeLevels.Num()) return false;
        for (int32 Index = 0; Index < NativeLevels.Num(); ++Index)
            if (World->GetLevels()[Index] != NativeLevels[Index]) return false;
        for (int32 Index = 0; Index < Levels.Num(); ++Index)
            if (Levels[Index]->Actors != Arrays[Index] || !CityLCER::Exact(Levels[Index]->GetPathName(), LevelPaths[Index])) return false;
        if (!CityLCER::Exact(World->GetPathName(), WorldPath) || !CityLCER::Exact(WorldTypeName(World->WorldType), Type)) return false;
        Actors.Sort([](const FObject& Left, const FObject& Right)
            { return CityLCER::Less(Left->GetStringField(TEXT("actor_path")), Right->GetStringField(TEXT("actor_path"))); });
        TArray<FValue> ActorValues;
        for (const auto& Actor : Actors) ActorValues.Add(MakeShared<FJsonValueObject>(Actor));
        const auto Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("world_path"), WorldPath);
        Row->SetStringField(TEXT("world_type"), Type);
        Row->SetField(TEXT("game_mode_class"), StringOrNull(World->GetAuthGameMode()
            ? World->GetAuthGameMode()->GetClass()->GetPathName() : FString()));
        Row->SetNumberField(TEXT("actor_array_size"), Slot);
        Row->SetArrayField(TEXT("visited_slots"), Visited);
        Row->SetArrayField(TEXT("null_slots"), Nulls);
        Row->SetArrayField(TEXT("actors"), ActorValues);
        Worlds.Add(MakeShared<FJsonValueObject>(Row));
    }
    if (GEngine->GetWorldContexts().Num() != Contexts.Num()) return false;
    int32 Index = 0;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (&Context != Contexts[Index] || Context.World() != ContextWorlds[Index]) return false;
        ++Index;
    }
    return true;
}
}

ACityLiveEvidenceGameMode::ACityLiveEvidenceGameMode()
{
    DefaultPawnClass = nullptr;
    SpectatorClass = nullptr;
    PlayerControllerClass = APlayerController::StaticClass();
    ReplaySpectatorPlayerControllerClass = APlayerController::StaticClass();
    HUDClass = nullptr;
    bStartPlayersAsSpectators = true;
    // Tick is reserved for dispatch of bytes read from the original stdin pipe
    // and completion of that command's pending Actor destruction.
    PrimaryActorTick.bCanEverTick = true;
    AutoReceiveInput = EAutoReceiveInput::Disabled;
}

ACityLiveEvidenceGameMode::~ACityLiveEvidenceGameMode() = default;

void ACityLiveEvidenceGameMode::BeginPlay()
{
    Super::BeginPlay();
}

bool ACityLiveEvidenceGameMode::Startup()
{
    if (!IsInGameThread() || bStartupSent || StartupRecord.IsValid() || !GetWorld()) return false;
    TArray<FValue> Arguments;
    FObject Environment(nullptr);
    if (!PlatformLaunchInputs(Arguments, Environment) || Arguments.Num() != 13) return false;
    const TCHAR* Fixed[] = {
        TEXT("/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"),
        TEXT("/Users/boandersson/Projects/CITY/CityMaterializationProof/CityMaterializationProof.uproject"),
        TEXT("/Engine/Maps/Entry?game=/Script/CityLiveEvidenceProof.CityLiveEvidenceGameMode"),
        TEXT("-game"), TEXT("-unattended"), TEXT("-nosplash"), TEXT("-NoSound"), TEXT("-log")};
    for (int32 Index = 0; Index < 8; ++Index)
        if (!CityLCER::Exact(Arguments[Index]->AsString(), Fixed[Index])) return false;
    const auto ReadRouting = [&Arguments](int32 Index, const FString& Prefix, FString& Value) -> bool
    {
        const FString Argument = Arguments[Index]->AsString();
        if (!Argument.StartsWith(Prefix, ESearchCase::CaseSensitive)) return false;
        Value = Argument.Mid(Prefix.Len());
        return !Value.IsEmpty();
    };
    if (!ReadRouting(8, TEXT("-LCERDomain="), Domain) ||
        !ReadRouting(9, TEXT("-LCERWitness="), Witness) ||
        !ReadRouting(10, TEXT("-LCERLaunch="), Launch) ||
        !ReadRouting(11, TEXT("-LCERRoot="), RuntimeRoot) ||
        (!CityLCER::Exact(Domain, TEXT("domain_A")) && !CityLCER::Exact(Domain, TEXT("domain_B"))) ||
        !CityLCER::Exact(Arguments[12]->AsString(), TEXT("-UserDir=") + RuntimeRoot + TEXT("/user"))) return false;
    // Paths and environment are checked as process provenance. Their values
    // never select canonical data, interaction output or a fault action.
    const auto OrdinaryDirectory = [](const FString& Path) -> bool
    {
        FTCHARToUTF8 Utf8(*Path);
        char Resolved[PATH_MAX];
        struct stat Info{};
        return realpath(Utf8.Get(), Resolved) && CityLCER::Exact(Path, UTF8_TO_TCHAR(Resolved)) &&
            lstat(Resolved, &Info) == 0 && S_ISDIR(Info.st_mode);
    };
    if (!OrdinaryDirectory(RuntimeRoot) || !OrdinaryDirectory(RuntimeRoot + TEXT("/home")) ||
        !OrdinaryDirectory(RuntimeRoot + TEXT("/user")) || !OrdinaryDirectory(RuntimeRoot + TEXT("/tmp"))) return false;
    const passwd* Operator = getpwuid(getuid());
    if (!Operator || !Operator->pw_name) return false;
    const FString User = UTF8_TO_TCHAR(Operator->pw_name);
    if (!CityLCER::Exact(Environment->GetStringField(TEXT("HOME")), RuntimeRoot + TEXT("/home")) ||
        !CityLCER::Exact(Environment->GetStringField(TEXT("TMPDIR")), RuntimeRoot + TEXT("/tmp")) ||
        !CityLCER::Exact(Environment->GetStringField(TEXT("USER")), User) || !CityLCER::Exact(Environment->GetStringField(TEXT("LOGNAME")), User) ||
        !CityLCER::Exact(Environment->GetStringField(TEXT("PATH")), TEXT("/usr/bin:/bin:/usr/sbin:/sbin")) ||
        !CityLCER::Exact(Environment->GetStringField(TEXT("LANG")), TEXT("C")) || !CityLCER::Exact(Environment->GetStringField(TEXT("LC_ALL")), TEXT("C"))) return false;
    struct proc_vnodepathinfo Vnodes{};
    if (proc_pidinfo(getpid(), PROC_PIDVNODEPATHINFO, 0, &Vnodes, sizeof(Vnodes)) != sizeof(Vnodes)) return false;
    const FString Cwd = UTF8_TO_TCHAR(Vnodes.pvi_cdir.vip_path);
    if (!CityLCER::Exact(Cwd, TEXT("/Users/boandersson/Projects/CITY"))) return false;
    TArray<FValue> Configs, Plugins, Images;
    FObject Module(nullptr);
    if (!PlatformConfigAndPlugins(Configs, Plugins) || !PlatformImages(Images, Module)) return false;
    TArray<FValue> Worlds, Controllers;
    TArray<FObject> Relevant;
    int32 PawnCount = 0;
    if (!CollectWorlds(Worlds, Controllers, Relevant, PawnCount) || !Relevant.IsEmpty() || PawnCount != 0 ||
        Controllers.Num() != 1 ||
        !CityLCER::Exact(Controllers[0]->AsObject()->GetStringField(TEXT("class_path")), TEXT("/Script/Engine.PlayerController")) ||
        !Controllers[0]->AsObject()->HasTypedField<EJson::Null>(TEXT("pawn_path"))) return false;
    int32 GameWorldCount = 0;
    for (const auto& Value : Worlds)
    {
        const auto World = Value->AsObject();
        if (CityLCER::Exact(World->GetStringField(TEXT("world_type")), TEXT("Game")))
        {
            ++GameWorldCount;
            if (!CityLCER::Exact(World->GetStringField(TEXT("world_path")), GetWorld()->GetPathName()) ||
                !CityLCER::Exact(GetWorld()->GetOutermost()->GetName(), TEXT("/Engine/Maps/Entry")) ||
                !World->HasTypedField<EJson::String>(TEXT("game_mode_class")) ||
                !CityLCER::Exact(World->GetStringField(TEXT("game_mode_class")), TEXT("/Script/CityLiveEvidenceProof.CityLiveEvidenceGameMode"))) return false;
        }
        for (const auto& Actor : World->GetArrayField(TEXT("actors")))
            if (Actor->AsObject()->GetNumberField(TEXT("auto_receive_input")) != 0) return false;
    }
    if (GameWorldCount != 1) return false;
    const auto Record = MakeShared<FJsonObject>();
    Record->SetStringField(TEXT("schema"), TEXT("city.live_evidence_startup.v1"));
    Record->SetStringField(TEXT("witness_id"), Witness);
    Record->SetStringField(TEXT("domain"), Domain);
    Record->SetStringField(TEXT("launch_id"), Launch);
    Record->SetNumberField(TEXT("pid"), getpid());
    Record->SetStringField(TEXT("cwd_realpath"), Cwd);
    Record->SetArrayField(TEXT("worlds"), Worlds);
    Record->SetArrayField(TEXT("controllers"), Controllers);
    Record->SetArrayField(TEXT("loaded_images"), Images);
    Record->SetArrayField(TEXT("enabled_plugins"), Plugins);
    Record->SetArrayField(TEXT("config_files"), Configs);
    Record->SetObjectField(TEXT("proof_module"), Module);
    StartupRecord = Record;
    Send(Record);
    return true;
}

void ACityLiveEvidenceGameMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bStartupSent)
    {
        if (!Startup()) { Fail(TEXT("lcer.startup_input_invalid")); return; }
        bStartupSent = true;
        InputWorker = MakeUnique<FLCERInputThread>(this);
        InputThread = FRunnableThread::Create(InputWorker.Get(), TEXT("CityLCEROriginalStdin"));
        if (!InputThread) { Fail(TEXT("lcer.original_pipe_closed")); return; }
    }
    FString Line;
    while (Input.Dequeue(Line)) Dispatch(Line);
    // This continuation belongs only to an already accepted stdin command.
    if (PendingCommand.IsValid()) ContinueMaterialization();
}

void ACityLiveEvidenceGameMode::EndPlay(const EEndPlayReason::Type Reason)
{
    if (InputWorker) InputWorker->Stop();
    if (InputThread)
    {
        InputThread->WaitForCompletion();
        delete InputThread;
        InputThread = nullptr;
    }
    InputWorker.Reset();
    Super::EndPlay(Reason);
}

void ACityLiveEvidenceGameMode::EnqueueInput(FString Line)
{
    Input.Enqueue(MoveTemp(Line));
}

void ACityLiveEvidenceGameMode::Send(const FObject& Object)
{
    const FString Raw = CityLCER::Stored(Object);
    if (Raw.IsEmpty()) { Fail(TEXT("lcer.schema_invalid")); return; }
    FTCHARToUTF8 Bytes(*Raw);
    ssize_t Offset = 0;
    while (Offset < Bytes.Length())
    {
        const ssize_t Written = write(STDOUT_FILENO, Bytes.Get() + Offset, Bytes.Length() - Offset);
        if (Written < 0 && errno == EINTR) continue;
        if (Written <= 0) { Fail(TEXT("lcer.original_pipe_closed")); return; }
        Offset += Written;
    }
}

void ACityLiveEvidenceGameMode::Fail(const FString& Error)
{
    bTerminal = true;
    FTCHARToUTF8 Bytes(*(Error + TEXT("\n")));
    const ssize_t Ignored = write(STDERR_FILENO, Bytes.Get(), Bytes.Length());
    (void)Ignored;
    // This terminates only this task-owned child. It never controls services.
    _exit(2);
}

void ACityLiveEvidenceGameMode::Respond(const FObject& Command, const FObject& Payload, const FString& Error)
{
    const auto Response = MakeShared<FJsonObject>();
    for (const TCHAR* Field : {TEXT("witness_id"), TEXT("domain"), TEXT("launch_id"), TEXT("operation_id"), TEXT("binding_sha256"), TEXT("command")})
        Response->SetStringField(Field, Command->GetStringField(Field));
    Response->SetStringField(TEXT("schema"), TEXT("city.live_evidence_response.v1"));
    Response->SetStringField(TEXT("status"), Error.IsEmpty() ? TEXT("ok") : TEXT("error"));
    if (Error.IsEmpty())
    {
        if (!Payload.IsValid()) { Fail(TEXT("lcer.schema_invalid")); return; }
        Response->SetField(TEXT("error"), MakeShared<FJsonValueNull>());
        Response->SetObjectField(TEXT("payload"), Payload);
    }
    else
    {
        bTerminal = true;
        PendingCommand.Reset();
        PendingRaw.Reset();
        PendingGeneration = -1;
        bAwaitingDestruction = false;
        const auto Failure = MakeShared<FJsonObject>();
        Failure->SetStringField(TEXT("code"), Error);
        Failure->SetStringField(TEXT("underlying_code"), Error);
        Failure->SetStringField(TEXT("stage"), Command->GetStringField(TEXT("operation_id")));
        Response->SetObjectField(TEXT("error"), Failure);
        Response->SetField(TEXT("payload"), MakeShared<FJsonValueNull>());
    }
    Send(Response);
}

void ACityLiveEvidenceGameMode::Dispatch(const FString& Line)
{
    FObject Command(nullptr);
    if (!CityLCER::Parse(Line, Command) || !CityLCER::Keys(Command, {TEXT("schema"), TEXT("witness_id"), TEXT("domain"), TEXT("launch_id"),
        TEXT("operation_id"), TEXT("binding_sha256"), TEXT("command"), TEXT("payload")})) { Fail(TEXT("lcer.schema_invalid")); return; }
    for (const TCHAR* Field : {TEXT("schema"), TEXT("witness_id"), TEXT("domain"), TEXT("launch_id"), TEXT("operation_id"), TEXT("binding_sha256"), TEXT("command")})
        if (!Command->HasTypedField<EJson::String>(Field)) { Fail(TEXT("lcer.schema_invalid")); return; }
    const FString Kind = Command->GetStringField(TEXT("command"));
    const FString Operation = Command->GetStringField(TEXT("operation_id"));
    if (!CityLCER::Exact(Command->GetStringField(TEXT("schema")), TEXT("city.live_evidence_command.v1")) ||
        (!CityLCER::Exact(Kind, TEXT("bind")) && !CityLCER::Exact(Kind, TEXT("materialize")) && !CityLCER::Exact(Kind, TEXT("emit")) && !CityLCER::Exact(Kind, TEXT("inspect")) &&
         !CityLCER::Exact(Kind, TEXT("arm_fault")) && !CityLCER::Exact(Kind, TEXT("shutdown")))) { Fail(TEXT("lcer.schema_invalid")); return; }
    if (!CityLCER::Exact(Command->GetStringField(TEXT("witness_id")), Witness) || !CityLCER::Exact(Command->GetStringField(TEXT("domain")), Domain) ||
        !CityLCER::Exact(Command->GetStringField(TEXT("launch_id")), Launch) ||
        (bBound && !CityLCER::Exact(Command->GetStringField(TEXT("binding_sha256")), BindingHash)))
    {
        Respond(Command, nullptr, TEXT("lcer.binding_mismatch"));
        return;
    }
    if (PendingCommand.IsValid() || CityLCER::Contains(Operations, Operation) || (!bBound && !CityLCER::Exact(Kind, TEXT("bind"))) ||
        (bTerminal && !CityLCER::Exact(Kind, TEXT("inspect")) && !CityLCER::Exact(Kind, TEXT("shutdown"))))
    {
        Respond(Command, nullptr, TEXT("lcer.operation_sequence_invalid"));
        return;
    }
    const bool bInspect = CityLCER::Exact(Operation, TEXT("inspect_L0")) || CityLCER::Exact(Operation, TEXT("inspect_L1")) || CityLCER::Exact(Operation, TEXT("inspect_L2")) ||
        CityLCER::Exact(Operation, TEXT("inspect_L3")) || CityLCER::Exact(Operation, TEXT("inspect_L4")) || CityLCER::Exact(Operation, TEXT("inspect_L5")) || CityLCER::Exact(Operation, TEXT("inspect_terminal"));
    if (!((CityLCER::Exact(Kind, TEXT("bind")) && CityLCER::Exact(Operation, TEXT("bind_0001"))) ||
        (CityLCER::Exact(Kind, TEXT("materialize")) && (CityLCER::Exact(Operation, TEXT("materialize_0001")) || CityLCER::Exact(Operation, TEXT("materialize_0002")))) ||
        (CityLCER::Exact(Kind, TEXT("emit")) && CityLCER::Exact(Operation, TEXT("emit_0001"))) || (CityLCER::Exact(Kind, TEXT("inspect")) && bInspect) ||
        (CityLCER::Exact(Kind, TEXT("arm_fault")) && CityLCER::Exact(Operation, TEXT("arm_fault_0001"))) || (CityLCER::Exact(Kind, TEXT("shutdown")) && CityLCER::Exact(Operation, TEXT("shutdown_0001")))))
    {
        Respond(Command, nullptr, TEXT("lcer.operation_sequence_invalid"));
        return;
    }
    if ((CityLCER::Exact(Kind, TEXT("emit")) || CityLCER::Exact(Kind, TEXT("inspect")) || CityLCER::Exact(Kind, TEXT("shutdown"))) &&
        !Command->HasTypedField<EJson::Null>(TEXT("payload")))
    {
        Respond(Command, nullptr, TEXT("lcer.schema_invalid"));
        return;
    }
    Operations.Add(Operation);
    FObject Result(nullptr);
    FString Error;
    if (CityLCER::Exact(Kind, TEXT("bind")))
    {
        if (!Bind(Command, Result, Error)) Respond(Command, nullptr, Error);
        else Respond(Command, Result, FString());
    }
    else if (CityLCER::Exact(Kind, TEXT("materialize"))) Materialize(Command);
    else if (CityLCER::Exact(Kind, TEXT("emit")))
    {
        if (bEmitted || CurrentGeneration != 0 || !Resource || !Anchor || !Resource->Interact(Routing(Operation), Result))
        {
            Respond(Command, nullptr, TEXT("lcer.operation_sequence_invalid"));
            return;
        }
        bEmitted = true;
        // Both the physical event and response are emitted before the parent
        // can issue the peer's interaction command.
        Send(Result->GetObjectField(TEXT("physical_event")));
        Respond(Command, Result, FString());
    }
    else if (CityLCER::Exact(Kind, TEXT("inspect")))
    {
        Result = Observe(Operation);
        Respond(Command, Result, Result.IsValid() ? FString() : TEXT("lcer.live_census_incomplete"));
    }
    else if (CityLCER::Exact(Kind, TEXT("arm_fault")))
    {
        if (!ArmFault(Command, Result, Error)) Respond(Command, nullptr, Error);
        else Respond(Command, Result, FString());
    }
    else
    {
        if (ArmedFault.IsValid() && !bFaultConsumed)
        {
            Respond(Command, nullptr, TEXT("lcer.fault_arm_unused"));
            Fail(TEXT("lcer.fault_arm_unused"));
            return;
        }
        Result = Routing(Operation);
        Result->SetStringField(TEXT("schema"), TEXT("city.live_evidence_shutdown_ack.v1"));
        Result->SetBoolField(TEXT("accepted"), true);
        Respond(Command, Result, FString());
        bTerminal = true;
        FPlatformMisc::RequestExit(false);
    }
}

void ACityLiveEvidenceGameMode::RestartPlayer(AController* NewPlayer)
{
    // The frozen proof world has one inert controller and no Pawn path.
}

TSharedPtr<FJsonObject> ACityLiveEvidenceGameMode::Routing(const FString& Operation) const
{
    const auto Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("witness_id"), Witness);
    Result->SetStringField(TEXT("domain"), Domain);
    Result->SetStringField(TEXT("launch_id"), Launch);
    Result->SetStringField(TEXT("operation_id"), Operation);
    Result->SetStringField(TEXT("binding_sha256"), BindingHash);
    return Result;
}

TSharedPtr<FJsonObject> ACityLiveEvidenceGameMode::Observe(const FString& Operation) const
{
    TArray<FValue> Worlds;
    TArray<FValue> Controllers;
    TArray<FObject> Relevant;
    int32 PawnCount = 0;
    if (!CollectWorlds(Worlds, Controllers, Relevant, PawnCount) || Worlds.IsEmpty()) return nullptr;
    FString Selected = Worlds[0]->AsObject()->GetStringField(TEXT("world_path"));
    for (const auto& Value : Worlds)
    {
        const auto World = Value->AsObject();
        if (CityLCER::Exact(World->GetStringField(TEXT("world_type")), TEXT("Game")))
        {
            Selected = World->GetStringField(TEXT("world_path"));
            break;
        }
    }
    TArray<FString> Ids;
    TArray<FObject> Resources;
    int32 Anchors = 0;
    for (const auto& Row : Relevant)
    {
        Ids.Add(Row->GetStringField(TEXT("actor_id")));
        FString Role;
        Row->TryGetStringField(TEXT("role"), Role);
        if (CityLCER::Exact(Role, TEXT("head_anchor"))) ++Anchors;
        if (CityLCER::Exact(Role, TEXT("resource_state"))) Resources.Add(Row);
    }
    Ids.Sort(CityLCER::Less);
    TArray<FValue> IdValues;
    for (const FString& Id : Ids) IdValues.Add(MakeShared<FJsonValueString>(Id));
    const auto CommonValue = [](const TArray<FObject>& Rows, const FString& Field) -> FValue
    {
        if (Rows.IsEmpty()) return MakeShared<FJsonValueNull>();
        const FValue First = Rows[0]->TryGetField(Field);
        const FString Identity = CityLCER::Canonical(First);
        for (const auto& Row : Rows)
            if (!CityLCER::Exact(CityLCER::Canonical(Row->TryGetField(Field)), Identity)) return MakeShared<FJsonValueNull>();
        return First;
    };
    // Only after the independent census is complete do routing fields attach.
    const auto Result = Routing(Operation);
    Result->SetStringField(TEXT("schema"), TEXT("city.live_evidence_observation.v1"));
    Result->SetArrayField(TEXT("worlds"), Worlds);
    Result->SetStringField(TEXT("selected_world_path"), Selected);
    Result->SetNumberField(TEXT("anchor_count"), Anchors);
    Result->SetNumberField(TEXT("resource_actor_count"), Resources.Num());
    Result->SetArrayField(TEXT("all_proof_actor_ids"), IdValues);
    Result->SetField(TEXT("record_sha256"), CommonValue(Relevant, TEXT("record_raw_sha256")));
    Result->SetField(TEXT("generation"), CommonValue(Relevant, TEXT("generation")));
    Result->SetField(TEXT("allocation_owner"), CommonValue(Resources, TEXT("allocation_owner")));
    return Result;
}

bool ACityLiveEvidenceGameMode::AuthenticateMaterialize(const FObject& Command, FString& Raw, int32& Generation, FString& Error)
{
    Error = TEXT("lcer.committed_record_required");
    if (!Command->HasTypedField<EJson::Object>(TEXT("payload"))) return false;
    const auto InputObject = Command->GetObjectField(TEXT("payload"));
    if (!CityLCER::Keys(InputObject, {TEXT("projection"), TEXT("record_raw_utf8"), TEXT("launch_receipt_raw_utf8")}) ||
        !InputObject->HasTypedField<EJson::Object>(TEXT("projection")) ||
        !InputObject->TryGetStringField(TEXT("record_raw_utf8"), Raw)) return false;
    FObject Record(nullptr);
    if (!CityLCER::Parse(Raw, Record)) return false;
    const FString RawHash = CityLCER::Digest(Raw);
    if (CityLCER::Exact(RawHash, TEXT("8cea1aa6ae3ab2d7a25b6b660c91c26d26a1340ab4f2b67e134f7b7feb12cb12"))) Generation = 0;
    else if (CityLCER::Exact(RawHash, TEXT("8e2862666a75833c8cff5c1faf9b783fb1d694de9df94fb5a4663fef599ea63c"))) Generation = 1;
    else return false;
    const auto Projection = InputObject->GetObjectField(TEXT("projection"));
    if (!CityLCER::Keys(Projection, {TEXT("schema"), TEXT("witness_id"), TEXT("domain"), TEXT("launch_id"), TEXT("operation_id"),
        TEXT("binding_sha256"), TEXT("record_role"), TEXT("record_raw_sha256"), TEXT("record_canonical_hash"),
        TEXT("generation"), TEXT("allocation_owner")})) return false;
    for (const TCHAR* Field : {TEXT("schema"), TEXT("witness_id"), TEXT("domain"), TEXT("launch_id"), TEXT("operation_id"),
        TEXT("binding_sha256"), TEXT("record_role"), TEXT("record_raw_sha256"), TEXT("record_canonical_hash")})
        if (!Projection->HasTypedField<EJson::String>(Field)) return false;
    if (!Projection->HasTypedField<EJson::Number>(TEXT("generation"))) return false;
    Error = TEXT("lcer.binding_mismatch");
    for (const TCHAR* Field : {TEXT("witness_id"), TEXT("domain"), TEXT("launch_id"), TEXT("operation_id"), TEXT("binding_sha256")})
        if (!CityLCER::Exact(Projection->GetStringField(Field), Command->GetStringField(Field))) return false;
    Error = TEXT("lcer.committed_record_required");
    const FString CanonicalHash = CityLCER::Digest(Raw.LeftChop(1));
    if (!CityLCER::Exact(Projection->GetStringField(TEXT("schema")), TEXT("city.live_evidence_projection.v1")) ||
        !CityLCER::Exact(Projection->GetStringField(TEXT("record_role")), (Generation == 0 ? TEXT("R0") : TEXT("R1"))) ||
        !CityLCER::Exact(Projection->GetStringField(TEXT("record_raw_sha256")), RawHash) ||
        !CityLCER::Exact(Projection->GetStringField(TEXT("record_canonical_hash")), CanonicalHash) ||
        Projection->GetNumberField(TEXT("generation")) != Generation) return false;
    if (Generation == 0)
    {
        if (!Projection->HasTypedField<EJson::Null>(TEXT("allocation_owner")) ||
            !InputObject->HasTypedField<EJson::String>(TEXT("launch_receipt_raw_utf8"))) return false;
        const auto Identity = Record->GetObjectField(TEXT("identity"));
        const auto Expected = MakeShared<FJsonObject>();
        Expected->SetStringField(TEXT("receipt_schema"), TEXT("ConcurrentUnrealLaunchReceipt.v1"));
        Expected->SetStringField(TEXT("artifact_role"), TEXT("canonical_materialization_input"));
        Expected->SetStringField(TEXT("raw_byte_sha256"), RawHash);
        Expected->SetStringField(TEXT("canonical_hash"), CanonicalHash);
        Expected->SetStringField(TEXT("expected_record_schema"), Identity->GetStringField(TEXT("record_schema")));
        Expected->SetStringField(TEXT("expected_payload_schema"), Identity->GetStringField(TEXT("payload_schema")));
        Expected->SetStringField(TEXT("expected_scenario_id"), Identity->GetStringField(TEXT("scenario_id")));
        Expected->SetStringField(TEXT("expected_simulation_version"), Identity->GetStringField(TEXT("simulation_version")));
        FObject Receipt(nullptr);
        const FString ReceiptRaw = InputObject->GetStringField(TEXT("launch_receipt_raw_utf8"));
        if (!CityLCER::Parse(ReceiptRaw, Receipt) || !CityLCER::Exact(ReceiptRaw, CityLCER::Stored(Expected))) return false;
    }
    else
    {
        // R1 uses its own committed successor law. The R0 launch validator is
        // never applied to R1 and no launch receipt is accepted for this step.
        if (!InputObject->HasTypedField<EJson::Null>(TEXT("launch_receipt_raw_utf8")) ||
            !Projection->HasTypedField<EJson::String>(TEXT("allocation_owner"))) return false;
        const FString Owner = Record->GetObjectField(TEXT("current_causal_state"))->GetObjectField(TEXT("shared_slot"))->GetStringField(TEXT("allocation_owner"));
        const auto Ancestry = Record->GetObjectField(TEXT("causal_provenance"))->GetObjectField(TEXT("canonical_ancestry"));
        if (!CityLCER::Exact(Owner, TEXT("domain_A")) || !CityLCER::Exact(Projection->GetStringField(TEXT("allocation_owner")), Owner) ||
            R0Raw.IsEmpty() || !CityLCER::Exact(Ancestry->GetStringField(TEXT("parent_record_hash")), CityLCER::Digest(R0Raw.LeftChop(1))) ||
            !CityLCER::Exact(Ancestry->GetStringField(TEXT("boundary_derivation")), TEXT("external_arbitration_batch"))) return false;
    }
    Error = TEXT("lcer.immediate_successor_required");
    const FString Operation = Command->GetStringField(TEXT("operation_id"));
    if (CityLCER::Exact(Operation, TEXT("materialize_0001")))
    {
        if (Generation != 0 || CurrentGeneration != -1 || bEmitted || !bBound) return false;
    }
    else if (CityLCER::Exact(Operation, TEXT("materialize_0002")))
    {
        if (Generation != 1 || CurrentGeneration != 0 || !bEmitted || !bBound) return false;
    }
    else return false;
    Error.Empty();
    return true;
}

bool ACityLiveEvidenceGameMode::Bind(const FObject& Command, FObject& Result, FString& Error)
{
    Error = TEXT("lcer.binding_mismatch");
    if (bBound || !StartupRecord.IsValid() || !Command->HasTypedField<EJson::Object>(TEXT("payload"))) return false;
    const auto Supplied = Command->GetObjectField(TEXT("payload"));
    if (!CityLCER::Keys(Supplied, {TEXT("witness_id"), TEXT("domain"), TEXT("launch_id"), TEXT("pid"),
        TEXT("macos_birth_tuple"), TEXT("executable_realpath"), TEXT("executable_sha256"), TEXT("project_realpath"),
        TEXT("project_sha256"), TEXT("module_inventory_sha256"), TEXT("argv_sha256"), TEXT("environment_sha256"),
        TEXT("descriptor_map_sha256"), TEXT("process_root_realpath"), TEXT("cwd_sha256"), TEXT("startup_sha256"),
        TEXT("input_inventory_sha256")})) return false;
    struct proc_bsdinfo Process{};
    struct proc_vnodepathinfo Vnodes{};
    char ExecutablePath[PROC_PIDPATHINFO_MAXSIZE];
    if (proc_pidinfo(getpid(), PROC_PIDTBSDINFO, 0, &Process, sizeof(Process)) != sizeof(Process) ||
        proc_pidinfo(getpid(), PROC_PIDVNODEPATHINFO, 0, &Vnodes, sizeof(Vnodes)) != sizeof(Vnodes) ||
        proc_pidpath(getpid(), ExecutablePath, sizeof(ExecutablePath)) <= 0) return false;
    const FString Cwd = UTF8_TO_TCHAR(Vnodes.pvi_cdir.vip_path);
    if (!CityLCER::Exact(Cwd, TEXT("/Users/boandersson/Projects/CITY")) ||
        StartupRecord->GetNumberField(TEXT("pid")) != getpid() ||
        !CityLCER::Exact(StartupRecord->GetStringField(TEXT("cwd_realpath")), Cwd)) return false;
    TArray<FValue> Arguments;
    FObject Environment(nullptr);
    TArray<FValue> Descriptors;
    if (!PlatformLaunchInputs(Arguments, Environment) || Arguments.Num() != 13 ||
        !PlatformProofDescriptors(Descriptors)) return false;
    const auto Executable = PlatformFileIdentity(UTF8_TO_TCHAR(ExecutablePath));
    const auto Project = PlatformFileIdentity(Arguments[1]->AsString());
    if (!Executable.IsValid() || !Project.IsValid()) return false;
    const auto Birth = MakeShared<FJsonObject>();
    Birth->SetNumberField(TEXT("seconds"), static_cast<double>(Process.pbi_start_tvsec));
    Birth->SetNumberField(TEXT("microseconds"), static_cast<double>(Process.pbi_start_tvusec));
    const auto Inputs = MakeShared<FJsonObject>();
    for (const TCHAR* Field : {TEXT("loaded_images"), TEXT("enabled_plugins"), TEXT("config_files")})
        Inputs->SetArrayField(Field, StartupRecord->GetArrayField(Field));
    Inputs->SetObjectField(TEXT("proof_module"), StartupRecord->GetObjectField(TEXT("proof_module")));
    const auto Expected = MakeShared<FJsonObject>();
    Expected->SetStringField(TEXT("witness_id"), Witness);
    Expected->SetStringField(TEXT("domain"), Domain);
    Expected->SetStringField(TEXT("launch_id"), Launch);
    Expected->SetNumberField(TEXT("pid"), Process.pbi_pid);
    Expected->SetObjectField(TEXT("macos_birth_tuple"), Birth);
    Expected->SetStringField(TEXT("executable_realpath"), Executable->GetStringField(TEXT("realpath")));
    Expected->SetStringField(TEXT("executable_sha256"), Executable->GetStringField(TEXT("sha256")));
    Expected->SetStringField(TEXT("project_realpath"), Project->GetStringField(TEXT("realpath")));
    Expected->SetStringField(TEXT("project_sha256"), Project->GetStringField(TEXT("sha256")));
    Expected->SetStringField(TEXT("module_inventory_sha256"), CityLCER::Digest(
        CityLCER::Canonical(MakeShared<FJsonValueArray>(StartupRecord->GetArrayField(TEXT("loaded_images")))) + TEXT("\n")));
    Expected->SetStringField(TEXT("argv_sha256"), CityLCER::Digest(CityLCER::Canonical(MakeShared<FJsonValueArray>(Arguments)) + TEXT("\n")));
    Expected->SetStringField(TEXT("environment_sha256"), CityLCER::Digest(CityLCER::Stored(Environment)));
    Expected->SetStringField(TEXT("descriptor_map_sha256"), CityLCER::Digest(CityLCER::Canonical(MakeShared<FJsonValueArray>(Descriptors)) + TEXT("\n")));
    Expected->SetStringField(TEXT("process_root_realpath"), RuntimeRoot);
    Expected->SetStringField(TEXT("cwd_sha256"), CityLCER::Digest(CityLCER::Canonical(MakeShared<FJsonValueString>(Cwd)) + TEXT("\n")));
    Expected->SetStringField(TEXT("startup_sha256"), CityLCER::Digest(CityLCER::Stored(StartupRecord)));
    Expected->SetStringField(TEXT("input_inventory_sha256"), CityLCER::Digest(CityLCER::Stored(Inputs)));
    const FString Raw = CityLCER::Stored(Supplied);
    const FString Hash = CityLCER::Digest(Raw);
    if (!CityLCER::Exact(Raw, CityLCER::Stored(Expected)) || !CityLCER::Exact(Hash, Command->GetStringField(TEXT("binding_sha256")))) return false;
    Binding = Expected;
    BindingHash = Hash;
    bBound = true;
    Result = Routing(TEXT("bind_0001"));
    Result->SetStringField(TEXT("schema"), TEXT("city.live_evidence_bind_ack.v1"));
    Result->SetStringField(TEXT("startup_sha256"), Expected->GetStringField(TEXT("startup_sha256")));
    Error.Empty();
    return true;
}

bool ACityLiveEvidenceGameMode::FaultReady(const FString& Stage) const
{
    if (bTerminal || bFaultConsumed || !bBound || !bEmitted || CurrentGeneration != 1 || PendingGeneration != 1 ||
        !ArmedFault.IsValid() || !PendingCommand.IsValid()) return false;
    FString Case;
    FString ArmedStage;
    FString ArmedOperation;
    FString PendingOperation;
    if (!ArmedFault->TryGetStringField(TEXT("failure_case"), Case) ||
        !ArmedFault->TryGetStringField(TEXT("stage"), ArmedStage) ||
        !ArmedFault->TryGetStringField(TEXT("operation_id"), ArmedOperation) ||
        !PendingCommand->TryGetStringField(TEXT("operation_id"), PendingOperation)) return false;
    if (!CityLCER::Exact(Case, Witness) || !CityLCER::Exact(ArmedStage, Stage) ||
        !CityLCER::Exact(ArmedOperation, TEXT("materialize_0002")) ||
        !CityLCER::Exact(PendingOperation, ArmedOperation)) return false;
    const bool bPartial = CityLCER::Exact(Case, TEXT("F13")) || CityLCER::Exact(Case, TEXT("F14"));
    const bool bAfterReceipt = CityLCER::Exact(Case, TEXT("F15")) || CityLCER::Exact(Case, TEXT("F16a")) || CityLCER::Exact(Case, TEXT("F16b"));
    return (bPartial || bAfterReceipt) &&
        CityLCER::Exact(Domain, CityLCER::Exact(Case, TEXT("F14")) ? TEXT("domain_B") : TEXT("domain_A")) &&
        CityLCER::Exact(Stage, bPartial ? TEXT("after_resource_before_anchor") : TEXT("after_receipt_before_observation"));
}

bool ACityLiveEvidenceGameMode::ArmFault(const FObject& Command, FObject& Result, FString& Error)
{
    Error = TEXT("lcer.fault_arm_invalid");
    if (ArmedFault.IsValid() || bFaultConsumed || CurrentGeneration != 0 || !bEmitted ||
        !Command->HasTypedField<EJson::Object>(TEXT("payload"))) return false;
    const auto Arm = Command->GetObjectField(TEXT("payload"));
    if (!CityLCER::Keys(Arm, {TEXT("failure_case"), TEXT("stage"), TEXT("operation_id")})) return false;
    for (const TCHAR* Field : {TEXT("failure_case"), TEXT("stage"), TEXT("operation_id")})
        if (!Arm->HasTypedField<EJson::String>(Field)) return false;
    const FString Case = Arm->GetStringField(TEXT("failure_case"));
    const FString Stage = Arm->GetStringField(TEXT("stage"));
    if (!CityLCER::Exact(Case, Witness) || !CityLCER::Exact(Arm->GetStringField(TEXT("operation_id")), TEXT("materialize_0002"))) return false;
    const bool bPartial = CityLCER::Exact(Case, TEXT("F13")) || CityLCER::Exact(Case, TEXT("F14"));
    const bool bAfterReceipt = CityLCER::Exact(Case, TEXT("F15")) || CityLCER::Exact(Case, TEXT("F16a")) || CityLCER::Exact(Case, TEXT("F16b"));
    if ((!bPartial && !bAfterReceipt) || !CityLCER::Exact(Domain, (CityLCER::Exact(Case, TEXT("F14")) ? TEXT("domain_B") : TEXT("domain_A"))) ||
        !CityLCER::Exact(Stage, (bPartial ? TEXT("after_resource_before_anchor") : TEXT("after_receipt_before_observation")))) return false;
    ArmedFault = Arm;
    Result = Routing(TEXT("arm_fault_0001"));
    Result->SetStringField(TEXT("schema"), TEXT("city.live_evidence_fault_ack.v1"));
    Result->SetStringField(TEXT("failure_case"), Case);
    Result->SetStringField(TEXT("stage"), Stage);
    Result->SetStringField(TEXT("armed_for"), TEXT("materialize_0002"));
    Error.Empty();
    return true;
}

void ACityLiveEvidenceGameMode::Materialize(const FObject& Command)
{
    if (bTerminal)
    {
        Respond(Command, nullptr, TEXT("lcer.operation_sequence_invalid"));
        return;
    }
    FString Error;
    FString Raw;
    int32 Generation = -1;
    if (!AuthenticateMaterialize(Command, Raw, Generation, Error))
    {
        Respond(Command, nullptr, Error);
        return;
    }
    PendingCommand = Command;
    PendingRaw = Raw;
    PendingGeneration = Generation;
    if (Generation == 1)
    {
        if (!Resource || !Anchor || !Resource->IsValidLowLevel() || !Anchor->IsValidLowLevel())
        {
            PendingCommand.Reset();
            Respond(Command, nullptr, TEXT("lcer.live_actor_cardinality_mismatch"));
            return;
        }
        Resource->DisableProposals();
        // Destruction is reached only after raw record, binding and lifecycle
        // validation. No rejected projection can erase the old representation.
        Anchor->Destroy();
        Resource->Destroy();
        Anchor = nullptr;
        Resource = nullptr;
        bAwaitingDestruction = true;
    }
    ContinueMaterialization();
}

void ACityLiveEvidenceGameMode::ContinueMaterialization()
{
    if (bTerminal || !PendingCommand.IsValid()) return;
    if (bAwaitingDestruction)
    {
        for (ULevel* Level : GetWorld()->GetLevels())
            for (AActor* Actor : Level->Actors)
                if (Actor && Actor->IsA<ACityLiveEvidenceActor>()) return;
        bAwaitingDestruction = false;
    }
    const auto Command = PendingCommand;
    const FString Operation = Command->GetStringField(TEXT("operation_id"));
    Resource = GetWorld()->SpawnActor<ACityLiveEvidenceResource>();
    if (!Resource || !Resource->Configure(TEXT("resource_state"), Domain, PendingRaw, PendingGeneration))
    {
        PendingCommand.Reset();
        Respond(Command, nullptr, TEXT("lcer.live_actor_cardinality_mismatch"));
        return;
    }
    CurrentRaw = PendingRaw;
    CurrentGeneration = PendingGeneration;
    if (CurrentGeneration == 0) R0Raw = CurrentRaw;
    else Resource->DisableProposals();
    if (ArmedFault.IsValid() && CityLCER::Exact(ArmedFault->GetStringField(TEXT("stage")), TEXT("after_resource_before_anchor")))
    {
        if (!FaultReady(TEXT("after_resource_before_anchor")))
        {
            PendingCommand.Reset();
            Respond(Command, nullptr, TEXT("lcer.fault_arm_invalid"));
            return;
        }
        const auto Before = Observe(Operation);
        const auto After = Observe(Operation);
        if (!Before.IsValid() || !After.IsValid() || !ConsumeFault(TEXT("after_resource_before_anchor"), Before, After))
        {
            PendingCommand.Reset();
            Respond(Command, nullptr, TEXT("lcer.fault_arm_invalid"));
            return;
        }
        // The actual new resource remains. No anchor is published or old pair
        // restored. The independent terminal census must expose that state.
        PendingCommand.Reset();
        Respond(Command, nullptr, TEXT("lcer.injected_partial_publication"));
        return;
    }
    Anchor = GetWorld()->SpawnActor<ACityLiveEvidenceHeadAnchor>();
    if (!Anchor || !Anchor->Configure(TEXT("head_anchor"), Domain, CurrentRaw, CurrentGeneration))
    {
        PendingCommand.Reset();
        Respond(Command, nullptr, TEXT("lcer.live_actor_cardinality_mismatch"));
        return;
    }
    const auto Result = MakeShared<FJsonObject>();
    FObject Record(nullptr);
    if (!CityLCER::Parse(CurrentRaw, Record))
    {
        PendingCommand.Reset();
        Respond(Command, nullptr, TEXT("lcer.committed_record_required"));
        return;
    }
    if (CurrentGeneration == 0)
    {
        const auto Contract = Record->GetObjectField(TEXT("current_causal_state"))->GetObjectField(TEXT("external_consequence_contracts"))->GetObjectField(Domain);
        const auto Acceptance = MakeShared<FJsonObject>();
        Acceptance->SetStringField(TEXT("receipt_schema"), TEXT("ConcurrentMaterializationAcceptanceReceipt.v1"));
        Acceptance->SetStringField(TEXT("process_instance_id"), Launch);
        Acceptance->SetStringField(TEXT("materialization_domain"), Resource->GetEvidenceDomain());
        Acceptance->SetStringField(TEXT("accepted_canonical_hash"), CityLCER::Digest(CurrentRaw.LeftChop(1)));
        Acceptance->SetStringField(TEXT("accepted_raw_payload_sha256"), Resource->GetRecordRawSha256());
        Acceptance->SetStringField(TEXT("materialized_physical_actor_id"), Contract->GetStringField(TEXT("physical_actor_id")));
        Acceptance->SetField(TEXT("materialized_shared_slot_owner"), StringOrNull(Resource->GetAllocationOwner()));
        Acceptance->SetBoolField(TEXT("proposal_capability_enabled"), Resource->bProposalCapability);
        Result->SetStringField(TEXT("r0_acceptance_raw_utf8"), CityLCER::Stored(Acceptance));
        Result->SetField(TEXT("r1_representation"), MakeShared<FJsonValueNull>());
    }
    else
    {
        const auto Receipt = Routing(Operation);
        Receipt->SetStringField(TEXT("schema"), TEXT("city.live_evidence_representation_receipt.v1"));
        Receipt->SetStringField(TEXT("record_raw_sha256"), Resource->GetRecordRawSha256());
        Receipt->SetStringField(TEXT("record_canonical_hash"), CityLCER::Digest(CurrentRaw.LeftChop(1)));
        Receipt->SetNumberField(TEXT("generation"), Resource->GetEvidenceGeneration());
        Receipt->SetStringField(TEXT("allocation_owner"), Resource->GetAllocationOwner());
        Receipt->SetStringField(TEXT("anchor_actor_id"), GetWorld()->GetPathName() + TEXT("|") + Anchor->GetPathName());
        Receipt->SetStringField(TEXT("resource_actor_id"), GetWorld()->GetPathName() + TEXT("|") + Resource->GetPathName());
        Receipt->SetBoolField(TEXT("proposal_capability_enabled"), Resource->bProposalCapability);
        Result->SetField(TEXT("r0_acceptance_raw_utf8"), MakeShared<FJsonValueNull>());
        Result->SetObjectField(TEXT("r1_representation"), Receipt);
    }
    if (ArmedFault.IsValid() && CityLCER::Exact(ArmedFault->GetStringField(TEXT("stage")), TEXT("after_receipt_before_observation")))
    {
        if (!FaultReady(TEXT("after_receipt_before_observation")))
        {
            PendingCommand.Reset();
            Respond(Command, nullptr, TEXT("lcer.fault_arm_invalid"));
            return;
        }
        const auto Before = Observe(Operation);
        const FString Case = ArmedFault->GetStringField(TEXT("failure_case"));
        if (CityLCER::Exact(Case, TEXT("F15"))) Resource->AllocationOwner = TEXT("domain_B");
        else
        {
            ACityLiveEvidenceResource* Extra = GetWorld()->SpawnActor<ACityLiveEvidenceResource>();
            const bool bOld = CityLCER::Exact(Case, TEXT("F16b"));
            if (!Extra || !Extra->Configure(TEXT("resource_state"), Domain, bOld ? R0Raw : CurrentRaw, bOld ? 0 : 1))
            {
                PendingCommand.Reset();
                Respond(Command, nullptr, TEXT("lcer.fault_arm_invalid"));
                return;
            }
            Extra->DisableProposals();
        }
        const auto After = Observe(Operation);
        if (!Before.IsValid() || !After.IsValid() || !ConsumeFault(TEXT("after_receipt_before_observation"), Before, After))
        {
            PendingCommand.Reset();
            Respond(Command, nullptr, TEXT("lcer.fault_arm_invalid"));
            return;
        }
        bTerminal = true;
    }
    PendingCommand.Reset();
    Respond(Command, Result, FString());
}

bool ACityLiveEvidenceGameMode::ConsumeFault(const FString& Stage, const FObject& Before, const FObject& After)
{
    if (!FaultReady(Stage)) return false;
    const FString Case = ArmedFault->GetStringField(TEXT("failure_case"));
    FString Action;
    FString Code;
    if (CityLCER::Exact(Case, TEXT("F13")))
    {
        Action = TEXT("Refresh A first. After successful R1 authentication, disable claim, destroy old Actors and wait for their absence; spawn R1 resource with domain_A owner. Consume fault before spawning anchor. Leave the one new resource in the world; do not restore R0.");
        Code = TEXT("lcer.injected_partial_publication");
    }
    else if (CityLCER::Exact(Case, TEXT("F14")))
    {
        Action = TEXT("Refresh B first. After successful R1 authentication, disable claim, destroy old Actors and wait for absence; spawn R1 resource. Consume fault before anchor. Leave the new resource; do not restore R0.");
        Code = TEXT("lcer.injected_partial_publication");
    }
    else if (CityLCER::Exact(Case, TEXT("F15")))
    {
        Action = TEXT("Refresh A first completely and construct a truthful R1 receipt. Consume hook after receipt construction but before response. Set only live resource allocation_owner to domain_B; emit the previously constructed receipt unaltered.");
        Code = TEXT("lcer.live_owner_mismatch");
    }
    else if (CityLCER::Exact(Case, TEXT("F16a")))
    {
        Action = TEXT("Refresh A first completely. Spawn one extra resource_state Actor with a new UObject path, same R1 record/generation/domain/owner. Keep original pair.");
        Code = TEXT("lcer.live_actor_cardinality_mismatch");
    }
    else if (CityLCER::Exact(Case, TEXT("F16b")))
    {
        Action = TEXT("Refresh A first completely. Spawn one extra resource_state Actor with a new UObject path, R0 record, generation 0 and null owner. Keep R1 pair.");
        Code = TEXT("lcer.live_generation_mismatch");
    }
    else return false;
    bFaultConsumed = true;
    const auto Event = MakeShared<FJsonObject>();
    Event->SetStringField(TEXT("failure_case"), Case);
    Event->SetStringField(TEXT("executor"), TEXT("unreal"));
    Event->SetStringField(TEXT("stage"), Stage);
    Event->SetStringField(TEXT("action"), Action);
    Event->SetBoolField(TEXT("consumed"), bFaultConsumed);
    Event->SetStringField(TEXT("underlying_code"), Code);
    const auto BeforeState = MakeShared<FJsonObject>();
    BeforeState->SetStringField(TEXT("kind"), TEXT("world"));
    BeforeState->SetObjectField(TEXT("observation"), Before);
    const auto AfterState = MakeShared<FJsonObject>();
    AfterState->SetStringField(TEXT("kind"), TEXT("world"));
    AfterState->SetObjectField(TEXT("observation"), After);
    Event->SetObjectField(TEXT("before"), BeforeState);
    Event->SetObjectField(TEXT("after"), AfterState);
    Send(Event);
    return true;
}
