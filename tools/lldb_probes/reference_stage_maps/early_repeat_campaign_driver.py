import os

import reference_stage_map_probe


ROOT = "/Volumes/Dev/L16_Lumen_ReverseEngineering"
LRIS = {
    28: "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri",
    35: "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri",
    70: "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri",
    150: "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri",
}
SITES = (0x26E4D5, 0x26E64F)


def run(debugger, focal, sample):
    if focal not in LRIS or sample < 3:
        raise ValueError((focal, sample))
    output_dir = f"{ROOT}/runs/reference_stage_maps/unit1_{focal}mm_repeat{sample:02d}"
    os.makedirs(output_dir, exist_ok=True)
    reference_stage_map_probe.reset(
        f"Unit-1 {focal}mm index-5 map repeat {sample}",
        output_dir,
        SITES,
        0x26E64F,
    )
    debugger.HandleCommand(
        "settings set target.env-vars "
        "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
        "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
    )
    debugger.HandleCommand("process handle SIGSEGV -p true -s false -n false")
    for site in SITES:
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{site:x}")
    reference_stage_map_probe.attach(debugger)
    debugger.HandleCommand(
        f'process launch -- "{LRIS[focal]}" "{output_dir}/output.dng" '
        "--profile 3 --export-fmt 4 --no-auto-lris"
    )
    reference_stage_map_probe.write_report(debugger, f"{output_dir}/report.json")
    process = debugger.GetSelectedTarget().GetProcess()
    if process.IsValid():
        process.Kill()
