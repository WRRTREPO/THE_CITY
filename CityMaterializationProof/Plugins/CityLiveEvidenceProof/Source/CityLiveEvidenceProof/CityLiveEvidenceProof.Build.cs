using UnrealBuildTool;

public class CityLiveEvidenceProof : ModuleRules
{
    public CityLiveEvidenceProof(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json", "Projects" });
        AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL");
    }
}
