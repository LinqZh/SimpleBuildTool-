#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import path, system, rename, remove
from subprocess import PIPE, Popen, CalledProcessError
from sys import stdout, exit
from tail import Tail
from time import asctime, localtime, time
from argparse import ArgumentParser
from configparser import ConfigParser
from _thread import start_new_thread
from re import sub

def print_build_log(txt: str):
    stdout.write(txt)
    stdout.flush()

def create_log_file(path: str):
    path = str.format("{}\\{}.log", path, sub(r'\s|:', '_' , time_now))
    with open(path, 'w') as log:
        return path

t: Tail

if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-c", "--codeVersion", help="Build task code version.", default="1.0.0")
    arg_parser.add_argument("-d", "--isDebug", help="Is debug mode.", default="Debug")
    arg_parser.add_argument("-r", "--isRename", help="Is rename package after build.", default="true")
    arg_parser.add_argument("-p", "--padType", help="Resouces dispatch mode.", default="None")
    arg_parser.add_argument("-o", "--overlayInstallType", help="Overlay install type.", default="None")
    args = arg_parser.parse_args()

    time_now = asctime(localtime(time()))
    parser = ConfigParser()
    dir = path.abspath(str.format("{}\\env.ini", path.dirname(__file__)))
    parser.read(dir, encoding="utf-8")
    unity = parser["global"]["unity"]
    project_path = parser["global"]["path"]
    log_path = create_log_file(parser["global"]["log"])
    mode = "assembleDebug"
    if args.padType == "Unity_Split_Pad":
        mode = "bundleDebug"
        if args.isDebug != "Debug":
            mode = "bundleRelease"
    elif args.isDebug != "Debug":
        mode = "assembleRelease"
        

    param_pass_parser = ConfigParser()
    param_pass_parser.add_section("buildParams")
    param_pass_parser.set("buildParams", "codeVersion", args.codeVersion)
    param_pass_parser.set("buildParams", "isDebug", args.isDebug)
    param_pass_parser.set("buildParams", "PadType", args.padType)
    param_pass_parser.set("buildParams", "OverlayInstallType", args.overlayInstallType)
    param_pass_path = str.format("{}\\Assets\\temp.ini", project_path)
    param_pass_parser.write(open(param_pass_path, 'w'))

    result = Popen('tasklist| findstr /i "Unity.exe"')
    result.wait()
    if result.returncode == 0:
        status = system('taskkill /IM "Unity.exe" /F')
        if status != 0:
            exit(status)

    result.kill()

    print_build_log("=============================================Start to unity build=============================================\n")

    cmd = str.format(
        "{} -quit -batchmode -projectPath {} -executeMethod LocalBuildTools.BuildApk -logFile {}",
        unity,
        project_path,
        log_path,
    )

    try:
        # https://www.jianshu.com/p/bd97cb8042a9
        def log_print(txt):
            print(txt)

        def tail_thread(file):
            global t
            try:
                t = Tail(file)
                t.register_callback(log_print)
                t.follow(s=1)
            except Exception as e:
                print(e)
                exit(1)

        start_new_thread(tail_thread, (log_path, ))

        process = Popen(cmd, shell=True, text=True, stdout=PIPE, stderr=PIPE)

        while True:
            out = process.stdout.read(1)
            if out == '' and process.poll() != None:
                break
            if out != '':
                print_build_log(out)

        process.communicate()
        t.isDispose = True
        if process.returncode == 0:
            print_build_log("=============================================Unity Build succeeded=============================================\n")
        else:
            print_build_log("=============================================Unity Build failed=============================================\n")
            process.kill()
            exit(1)
    
        process.kill()

    except CalledProcessError as e:
        print(e.stderr.decode())

    print_build_log("=============================================AS build started.=============================================\n")
    export_path = parser["global"]["output_path"]
    work_space = parser["global"]["work_space"]
    as_process = Popen(str.format("powershell {}\\AS_Build.ps1 {} {}", work_space, work_space, mode))
    as_process.communicate()
    if as_process.returncode != 0:
        print_build_log("=============================================AS build failed.=============================================\n")
    else:
        print_build_log("=============================================AS build finished.=============================================\n")
        if args.isRename == "true":
            param_pass_parser.read(param_pass_path, encoding="utf-8")

            package_name = param_pass_parser["buildOutput"]["packageName"]
            symbol = "apk"
            final_path = "debug"
            extension = "apk"

            if args.isDebug != "Debug":
                final_path = "release"

            if args.padType == "Unity_Split_Pad":
                package_name = param_pass_parser["buildOutput"]["aabName"]
                symbol = "bundle"
                extension = "aab"

            prefixion = str.format("{}\\launcher\\build\\outputs\\{}\\{}", export_path, symbol, final_path)
            package_path = str.format("{}\\launcher-{}.{}", prefixion, final_path, extension)
            if not path.exists(package_path):
                print_build_log("Can not find output package.")
                exit(1)

            rename(package_path, str.format("{}\\{}.{}", prefixion, package_name, extension))
    
    as_process.kill()

    remove(param_pass_path)
    meta_path = str.format("{}.meta", param_pass_path)
    if path.exists(meta_path):
        remove(meta_path)