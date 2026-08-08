import builtins
import json
from pathlib import Path


PATCH_VA = 0x36E515
PATCH = bytes.fromhex("0f57c090")
EXPECTED = bytes.fromhex("f30f51c0")
REPORT_PATH = None


def reset(report_path):
    global REPORT_PATH
    REPORT_PATH = Path(report_path)
    REPORT_PATH.unlink(missing_ok=True)


def write_report(packet):
    if REPORT_PATH is None:
        return
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")


def apply(frame, bp_loc, internal_dict):
    lldb = builtins.__import__("lldb")
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    header = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    address = header + PATCH_VA

    error = lldb.SBError()
    before = process.ReadMemory(address, 4, error)
    if not error.Success() or before != EXPECTED:
        packet = {
            "address": address,
            "before": before.hex() if before else None,
            "error": str(error),
            "verified": False,
        }
        write_report(packet)
        print(
            "L16_ZERO_SCORE_PATCH_ERROR",
            json.dumps(packet, sort_keys=True),
        )
        process.Kill()
        return False

    written = process.WriteMemory(address, PATCH, error)
    after = process.ReadMemory(address, 4, error)
    packet = {
        "libcp_header": header,
        "address": address,
        "before": before.hex(),
        "after": after.hex() if after else None,
        "written": written,
        "verified": error.Success() and written == 4 and after == PATCH,
    }
    write_report(packet)
    print("L16_ZERO_SCORE_PATCH", json.dumps(packet, sort_keys=True))
    if not packet["verified"]:
        process.Kill()
    return False
