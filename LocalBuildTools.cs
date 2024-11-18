using UnityEngine;
using UnityEditor;
using ET;
using BM;
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

public class LocalBuildTools
{
    [DllImport("kernel32")]
    private static extern int GetPrivateProfileString(string lpAppName, string lpKeyName, string lpDefault, StringBuilder returnBuilder, int size, string fileName);

    [DllImport("kernel32")]
    private static extern int WritePrivateProfileString(string lpApplicationName, string lpKeyName, string lpString, string lpFileName);

    private static string _path = "";
    private static FileStream _fs;
    
    [MenuItem("Tools/LocalBuild")]
    public static void BuildApk()
    {
        var tempSB = new StringBuilder(1024);
        _path = tempSB.Append(Application.dataPath).Append("\\temp.ini").ToString();
        bool isDebug = true;
        if (File.Exists(_path))
        {
            AssetsSetting.Instance.codeVersionName = GetIniSetting(tempSB, "buildParams", "codeVersion", "1.0.0");
            AssetsSetting.Instance.PackerType = GetPackerType(GetIniSetting(tempSB, "buildParams", "isDebug", "Debug"));
            isDebug = AssetsSetting.Instance.PackerType == PackerType.Debug;
            AssetsSetting.Instance.PadType = GetPadType(GetIniSetting(tempSB, "buildParams", "PadType", "None"));
            AssetsSetting.Instance.OverlayInstallType = GetOverlayInstallType(GetIniSetting(tempSB, "buildParams", "OverlayInstallType", "None"));
            Console.WriteLine(BFFramework.Utility.Text.Format("Read setting, version: {0}, isDebug: {1}", AssetsSetting.Instance.versionNum, isDebug));
            ResVersionHelper.FlushSetting();
        }
        StartBuild(PlatformType.Android/**/, BuildAssetBundleOptions.ChunkBasedCompression, BuildOptions.None, isDebug, true, true, true, true, AssetsSetting.Instance.PadType);
    }/**/

    private static string GetIniSetting(StringBuilder temp, string section, string name, string defaultValue)
    {
        temp.Clear();
        GetPrivateProfileString(section, name, defaultValue, temp, 1024, _path);
        return temp.ToString();
    }

    private static PackerType GetPackerType(string input)
    {
        switch (input)
        {
            case "Online":
                return PackerType.Online;
            case "Online1":
                return PackerType.Online1;
            case "Ios_Debug":
                return PackerType.Ios_Debug;
            case "Ios_Online":
                return PackerType.Ios_Online;
            default:
                return PackerType.Debug;
        }
    }
    
    private static PadType GetPadType(string input)
    {
        switch (input)
        {
            case "Google_Pad":
                return PadType.Google_Pad;
            case "Custom_Pad__Fast_follow":
                return PadType.Custom_Pad__Fast_follow;
            case "Unity_Split_Pad":
                return PadType.Unity_Split_Pad;
            default:
                return PadType.None;
        }
    }

    private static OverlayInstallType GetOverlayInstallType(string input)
    {
        switch (input)
        {
            case "Force":
                return OverlayInstallType.Force;
            case "Notice":
                return OverlayInstallType.Notice;
            default:
                return OverlayInstallType.None; 
        }
    }
    
    public static void StartBuild(PlatformType platformType, BuildAssetBundleOptions buildAssetBundleOptions, BuildOptions buildOptions, bool isDebug, bool isFullPackage, bool isBuildExe, bool isContainAB, bool clearFolder, PadType padType)
    {
        BuildHelper.Build(platformType, 
            buildAssetBundleOptions, 
            buildOptions,  
            isDebug, 
            isFullPackage,
            isBuildExe,
            isContainAB, 
            clearFolder, 
            "ackeydffghjhjkdsfdgcvm", 
            BuildHelper.IsGooglePad(padType));
        
        
        if (File.Exists(_path))
        {
            string packType = (AssetsSetting.Instance.PackerType.ToString().IndexOf("Debug") > -1) ? "Test" : "release";
            WritePrivateProfileString("buildOutput", "packageName", BFFramework.Utility.Text.Format("{0}_{1}_{2}{3}", BuildHelper.GetProgramName(), AssetsSetting.Instance.codeVersionName, packType, AssetsSetting.Instance.BuildTime), _path);
            WritePrivateProfileString("buildOutput", "aabName", BFFramework.Utility.Text.Format("{0}_{1}", BuildHelper.GetProgramName(), AssetsSetting.Instance.codeVersionName), _path);
        }
    }
}