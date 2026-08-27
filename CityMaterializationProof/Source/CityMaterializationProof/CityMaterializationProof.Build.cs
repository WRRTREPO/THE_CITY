using UnrealBuildTool;

public class CityMaterializationProof : ModuleRules
{
    public CityMaterializationProof(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "Json",
            "JsonUtilities"
        });
        AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL");
    }
}
