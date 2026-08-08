#!/usr/bin/env python3
"""Tool #4 — LRI Proto Field Decoder
Annotate any LRI block's proto payload with field names + types.
Core field names come from serialized FileDescriptorProto data in libcp.dylib.

Usage:
  python3 tools/lri_field_inspect.py \
    --lri /Volumes/.../L16_02130.lri \
    --block-index 0 \
    --proto-class LightHeader \
    [--depth 2] \
    [--field N] \
    [--json]
"""

import argparse
import json
import os
import re
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
STRINGS_FILE = REPO_ROOT / "libcp_strings_scratch.txt"
FIELD_MAP_CACHE = Path(__file__).parent / "proto_field_map.json"

# Core schema map extracted from libcp.dylib's serialized descriptors. Keep this
# aligned with verify_embedded_calibration_proto_schema.py.
BUILTIN_FIELD_MAP = {
    ("LightHeader", 1):  ("image_unique_id_low", "uint64", None),
    ("LightHeader", 2):  ("image_unique_id_high", "uint64", None),
    ("LightHeader", 3):  ("image_time_stamp", "TimeStamp", "TimeStamp"),
    ("LightHeader", 4):  ("image_focal_length", "int32", None),
    ("LightHeader", 5):  ("image_reference_camera", "CameraID", None),
    ("LightHeader", 6):  ("device_unique_id_low", "uint64", None),
    ("LightHeader", 7):  ("device_unique_id_high", "uint64", None),
    ("LightHeader", 8):  ("device_model_name", "string", None),
    ("LightHeader", 9):  ("device_fw_version", "string", None),
    ("LightHeader", 10): ("device_asic_fw_version", "string", None),
    ("LightHeader", 11): ("device_temperature", "DeviceTemp", "DeviceTemp"),
    ("LightHeader", 12): ("modules", "repeated CameraModule", "CameraModule"),
    ("LightHeader", 13): ("module_calibration", "repeated FactoryModuleCalibration", "FactoryModuleCalibration"),
    ("LightHeader", 14): ("device_calibration", "FactoryDeviceCalibration", "FactoryDeviceCalibration"),
    ("LightHeader", 15): ("gold_cc", "repeated ColorCalibrationGold", "ColorCalibrationGold"),
    ("LightHeader", 16): ("sensor_data", "repeated SensorData", "SensorData"),
    ("LightHeader", 17): ("tof_range", "float", None),
    ("LightHeader", 18): ("hw_info", "HwInfo", "HwInfo"),
    ("LightHeader", 19): ("view_preferences", "ViewPreferences", "ViewPreferences"),
    ("LightHeader", 20): ("proximity_sensors", "ProximitySensors", "ProximitySensors"),
    ("LightHeader", 22): ("flash_data", "FlashData", "FlashData"),
    ("LightHeader", 23): ("imu_data", "repeated IMUData", "IMUData"),
    ("LightHeader", 24): ("af_info", "AFDebugInfo", "AFDebugInfo"),
    ("LightHeader", 25): ("gps_data", "GPSData", "GPSData"),
    ("LightHeader", 26): ("compatibility", "Compatibility", "Compatibility"),
    ("LightHeader", 27): ("face_data", "repeated FaceData", "FaceData"),

    ("FactoryDeviceCalibration", 1): ("flash", "FlashCalibration", "FlashCalibration"),
    ("FactoryDeviceCalibration", 2): ("tof", "ToFCalibration", "ToFCalibration"),
    ("FactoryDeviceCalibration", 3): ("time_stamp", "TimeStamp", "TimeStamp"),

    ("SensorData", 1): ("type", "SensorType", None),
    ("SensorData", 2): ("data", "SensorCharacterization", "SensorCharacterization"),
    ("SensorData", 3): ("time_stamp", "TimeStamp", "TimeStamp"),
    ("SensorCharacterization", 1): ("black_level", "float", None),
    ("SensorCharacterization", 2): ("white_level", "float", None),
    ("SensorCharacterization", 3): ("cliff_slope", "float", None),
    ("SensorCharacterization", 4): ("vst_model", "repeated SensorCharacterization.VstNoiseModel", "SensorCharacterization.VstNoiseModel"),
    ("SensorCharacterization.VstNoiseModel", 1): ("gain", "uint32", None),
    ("SensorCharacterization.VstNoiseModel", 2): ("threshold", "float", None),
    ("SensorCharacterization.VstNoiseModel", 3): ("scale", "float", None),
    ("SensorCharacterization.VstNoiseModel", 4): ("red", "SensorCharacterization.VstNoiseModel.VstModel", "SensorCharacterization.VstNoiseModel.VstModel"),
    ("SensorCharacterization.VstNoiseModel", 5): ("green", "SensorCharacterization.VstNoiseModel.VstModel", "SensorCharacterization.VstNoiseModel.VstModel"),
    ("SensorCharacterization.VstNoiseModel", 6): ("blue", "SensorCharacterization.VstNoiseModel.VstModel", "SensorCharacterization.VstNoiseModel.VstModel"),
    ("SensorCharacterization.VstNoiseModel", 7): ("panchromatic", "SensorCharacterization.VstNoiseModel.VstModel", "SensorCharacterization.VstNoiseModel.VstModel"),
    ("SensorCharacterization.VstNoiseModel.VstModel", 1): ("a", "float", None),
    ("SensorCharacterization.VstNoiseModel.VstModel", 2): ("b", "float", None),

    ("FlashCalibration", 1): ("ledcool_lux", "float", None),
    ("FlashCalibration", 2): ("ledcool_max_lumens", "float", None),
    ("FlashCalibration", 3): ("ledcool_cct", "float", None),
    ("FlashCalibration", 4): ("ledwarm_lux", "float", None),
    ("FlashCalibration", 5): ("ledwarm_max_lumens", "float", None),
    ("FlashCalibration", 6): ("ledwarm_cct", "float", None),
    ("ToFCalibration", 1): ("offset_distance", "float", None),
    ("ToFCalibration", 2): ("offset_measurement", "float", None),
    ("ToFCalibration", 3): ("xtalk_distance", "float", None),
    ("ToFCalibration", 4): ("xtalk_measurement", "float", None),

    ("ViewPreferences", 1): ("f_number", "float", None),
    ("ViewPreferences", 2): ("ev_offset", "float", None),
    ("ViewPreferences", 3): ("disable_cropping", "bool", None),
    ("ViewPreferences", 4): ("hdr_mode", "ViewPreferences.HDRMode", None),
    ("ViewPreferences", 5): ("view_preset", "ViewPreferences.ViewPresets", None),
    ("ViewPreferences", 6): ("scene_mode", "ViewPreferences.SceneMode", None),
    ("ViewPreferences", 7): ("awb_mode", "ViewPreferences.AWBMode", None),
    ("ViewPreferences", 9): ("orientation", "ViewPreferences.Orientation", None),
    ("ViewPreferences", 10): ("image_gain", "float", None),
    ("ViewPreferences", 11): ("image_integration_time_ns", "uint64", None),
    ("ViewPreferences", 12): ("user_rating", "uint32", None),
    ("ViewPreferences", 13): ("aspect_ratio", "ViewPreferences.AspectRatio", None),
    ("ViewPreferences", 14): ("crop", "ViewPreferences.Crop", "ViewPreferences.Crop"),
    ("ViewPreferences", 15): ("awb_gains", "ViewPreferences.ChannelGain", "ViewPreferences.ChannelGain"),
    ("ViewPreferences", 16): ("is_on_tripod", "bool", None),
    ("ViewPreferences", 17): ("qc_lux_index", "float", None),
    ("ViewPreferences", 18): ("display_gain", "float", None),
    ("ViewPreferences", 19): ("display_integration_time_ns", "uint64", None),
    ("ViewPreferences.Crop", 1): ("start", "Point2F", "Point2F"),
    ("ViewPreferences.Crop", 2): ("size", "Point2F", "Point2F"),
    ("ViewPreferences.ChannelGain", 1): ("r", "float", None),
    ("ViewPreferences.ChannelGain", 2): ("g_r", "float", None),
    ("ViewPreferences.ChannelGain", 3): ("g_b", "float", None),
    ("ViewPreferences.ChannelGain", 4): ("b", "float", None),

    ("GPSData", 1): ("latitude", "double", None),
    ("GPSData", 2): ("longitude", "double", None),
    ("GPSData", 3): ("timestamp", "uint64", None),
    ("GPSData", 4): ("dop", "double", None),
    ("GPSData", 5): ("track", "GPSData.Track", "GPSData.Track"),
    ("GPSData", 6): ("heading", "GPSData.Heading", "GPSData.Heading"),
    ("GPSData", 7): ("altitude", "GPSData.Altitude", "GPSData.Altitude"),
    ("GPSData", 8): ("speed", "double", None),
    ("GPSData", 9): ("processing_method", "GPSData.ProcessingMethod", None),
    ("GPSData.Track", 1): ("value", "double", None),
    ("GPSData.Track", 2): ("ref", "GPSData.ReferenceNorth", None),
    ("GPSData.Heading", 1): ("value", "double", None),
    ("GPSData.Heading", 2): ("ref", "GPSData.ReferenceNorth", None),
    ("GPSData.Altitude", 1): ("value", "double", None),
    ("GPSData.Altitude", 2): ("ref", "GPSData.ReferenceAltitude", None),

    ("Point2F", 1): ("x", "float", None),
    ("Point2F", 2): ("y", "float", None),
    ("Point2I", 1): ("x", "sint32", None),
    ("Point2I", 2): ("y", "sint32", None),
    ("Point3F", 1): ("x", "float", None),
    ("Point3F", 2): ("y", "float", None),
    ("Point3F", 3): ("z", "float", None),

    ("CameraModule", 1):  ("af_info", "CameraModule.AFInfo", "CameraModule.AFInfo"),
    ("CameraModule", 2):  ("id", "CameraID", None),
    ("CameraModule", 3):  ("is_enabled", "bool", None),
    ("CameraModule", 4):  ("mirror_position", "int32", None),
    ("CameraModule", 5):  ("lens_position", "int32", None),
    ("CameraModule", 7):  ("sensor_analog_gain", "float", None),
    ("CameraModule", 8):  ("sensor_exposure", "uint64", None),
    ("CameraModule", 9):  ("sensor_data_surface", "CameraModule.Surface", "CameraModule.Surface"),
    ("CameraModule", 10): ("sensor_temparature", "sint32", None),
    ("CameraModule", 11): ("sensor_is_horizontal_flip", "bool", None),
    ("CameraModule", 12): ("sensor_is_vertical_flip", "bool", None),
    ("CameraModule", 13): ("sensor_bayer_red_override", "Point2I", "Point2I"),
    ("CameraModule", 14): ("sensor_digital_gain", "float", None),
    ("CameraModule", 15): ("frame_index", "uint32", None),
    ("CameraModule", 16): ("sensor_dpc_on", "bool", None),
    ("CameraModule", 17): ("sensor_exp_start_offset", "sint32", None),
    ("CameraModule", 18): ("sensor_scan_speed", "float", None),

    ("CameraModule.Surface", 1): ("start", "Point2I", "Point2I"),
    ("CameraModule.Surface", 2): ("size", "Point2I", "Point2I"),
    ("CameraModule.Surface", 3): ("format", "CameraModule.Surface.FormatType", None),
    ("CameraModule.Surface", 4): ("row_stride", "uint32", None),
    ("CameraModule.Surface", 5): ("data_offset", "uint64", None),
    ("CameraModule.Surface", 6): ("data_scale", "Point2F", "Point2F"),

    ("FactoryModuleCalibration", 1): ("camera_id", "CameraID", None),
    ("FactoryModuleCalibration", 2): ("color", "repeated ColorCalibration", "ColorCalibration"),
    ("FactoryModuleCalibration", 3): ("geometry", "GeometricCalibration", "GeometricCalibration"),
    ("FactoryModuleCalibration", 4): ("vignetting", "VignettingCharacterization", "VignettingCharacterization"),
    ("FactoryModuleCalibration", 5): ("hot_pixel_map", "HotPixelMap", "HotPixelMap"),
    ("FactoryModuleCalibration", 6): ("dead_pixel_map", "DeadPixelMap", "DeadPixelMap"),
    ("FactoryModuleCalibration", 7): ("time_stamp", "TimeStamp", "TimeStamp"),

    ("VignettingCharacterization", 1): ("crosstalk", "VignettingCharacterization.CrosstalkModel", "VignettingCharacterization.CrosstalkModel"),
    ("VignettingCharacterization", 2): ("vignetting", "repeated VignettingCharacterization.MirrorVignettingModel", "VignettingCharacterization.MirrorVignettingModel"),
    ("VignettingCharacterization", 3): ("relative_brightness", "float", None),
    ("VignettingCharacterization", 4): ("lens_hall_code", "int32", None),
    ("VignettingCharacterization.CrosstalkModel", 1): ("width", "uint32", None),
    ("VignettingCharacterization.CrosstalkModel", 2): ("height", "uint32", None),
    ("VignettingCharacterization.CrosstalkModel", 3): ("data", "repeated Matrix4x4F", "Matrix4x4F"),
    ("VignettingCharacterization.CrosstalkModel", 4): ("data_packed", "repeated float", None),
    ("VignettingCharacterization.VignettingModel", 1): ("width", "uint32", None),
    ("VignettingCharacterization.VignettingModel", 2): ("height", "uint32", None),
    ("VignettingCharacterization.VignettingModel", 3): ("data", "repeated float", None),
    ("VignettingCharacterization.MirrorVignettingModel", 1): ("hall_code", "int32", None),
    ("VignettingCharacterization.MirrorVignettingModel", 2): ("vignetting", "VignettingCharacterization.VignettingModel", "VignettingCharacterization.VignettingModel"),

    ("GeometricCalibration", 1): ("mirror_type", "GeometricCalibration.MirrorType", None),
    ("GeometricCalibration", 2): ("per_focus_calibration", "repeated GeometricCalibration.CalibrationFocusBundle", "GeometricCalibration.CalibrationFocusBundle"),
    ("GeometricCalibration", 3): ("distortion", "Distortion", "Distortion"),
    ("GeometricCalibration", 4): ("lens_hall_code_range", "Range2F", "Range2F"),
    ("GeometricCalibration", 5): ("focus_distance_range", "Range2F", "Range2F"),
    ("GeometricCalibration", 6): ("angle_optical_center_mapping", "GeometricCalibration.AngleOpticalCenterMapping", "GeometricCalibration.AngleOpticalCenterMapping"),

    ("GeometricCalibration.CalibrationFocusBundle", 1): ("focus_distance", "float", None),
    ("GeometricCalibration.CalibrationFocusBundle", 2): ("intrinsics", "GeometricCalibration.Intrinsics", "GeometricCalibration.Intrinsics"),
    ("GeometricCalibration.CalibrationFocusBundle", 3): ("extrinsics", "GeometricCalibration.Extrinsics", "GeometricCalibration.Extrinsics"),
    ("GeometricCalibration.CalibrationFocusBundle", 4): ("sensor_temp", "sint32", None),
    ("GeometricCalibration.CalibrationFocusBundle", 5): ("device_temp", "DeviceTemp", "DeviceTemp"),
    ("GeometricCalibration.CalibrationFocusBundle", 6): ("focus_hall_code", "float", None),

    ("GeometricCalibration.Intrinsics", 1): ("k_mat", "Matrix3x3F", "Matrix3x3F"),
    ("GeometricCalibration.Intrinsics", 2): ("rms_error", "float", None),
    ("GeometricCalibration.Extrinsics", 1): ("canonical", "GeometricCalibration.Extrinsics.CanonicalFormat", "GeometricCalibration.Extrinsics.CanonicalFormat"),
    ("GeometricCalibration.Extrinsics", 2): ("moveable_mirror", "GeometricCalibration.Extrinsics.MovableMirrorFormat", "GeometricCalibration.Extrinsics.MovableMirrorFormat"),
    ("GeometricCalibration.Extrinsics.CanonicalFormat", 1): ("rotation", "Matrix3x3F", "Matrix3x3F"),
    ("GeometricCalibration.Extrinsics.CanonicalFormat", 2): ("translation", "Point3F", "Point3F"),
    ("GeometricCalibration.Extrinsics.CanonicalFormat", 3): ("stereo_error", "float", None),
    ("GeometricCalibration.Extrinsics.CanonicalFormat", 4): ("reprojection_error", "float", None),

    ("HwInfo", 1): ("camera", "repeated CameraModuleHwInfo", "CameraModuleHwInfo"),
    ("HwInfo", 2): ("body_serial", "string", None),
    ("HwInfo", 3): ("tof", "ToFType", None),  # enum
    ("HwInfo", 4): ("firmware_version", "string", None),
    ("HwInfo", 5): ("pcb_rev", "string", None),

    ("CameraModuleHwInfo", 1): ("camera_id", "uint32", None),
    ("CameraModuleHwInfo", 2): ("module_serial", "string", None),
    ("CameraModuleHwInfo", 3): ("lens_type", "uint32", None),
    ("CameraModuleHwInfo", 4): ("calibration_date", "string", None),

    ("IMUData", 1): ("samples", "repeated IMUData_Sample", "IMUData_Sample"),
    ("IMUData", 2): ("timestamp_ns", "uint64", None),

    ("IMUData_Sample", 1): ("timestamp_ns", "uint64", None),
    ("IMUData_Sample", 2): ("accel_x", "float", None),
    ("IMUData_Sample", 3): ("accel_y", "float", None),
    ("IMUData_Sample", 4): ("accel_z", "float", None),
    ("IMUData_Sample", 5): ("gyro_x", "float", None),
    ("IMUData_Sample", 6): ("gyro_y", "float", None),
    ("IMUData_Sample", 7): ("gyro_z", "float", None),
}


# ── Protobuf utilities (standalone — does not import lri_protobuf_walker) ─────

def read_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
    raise ValueError("truncated varint")


def parse_proto_fields(data: bytes):
    """Yield (field_num, wire_type, raw_value) triples.
    raw_value: int for varint/fixed, bytes for len-delimited.
    """
    pos = 0
    while pos < len(data):
        try:
            tag, pos = read_varint(data, pos)
        except (ValueError, IndexError):
            break
        field_num = tag >> 3
        wire_type = tag & 0x7
        if field_num == 0:
            break
        if wire_type == 0:
            try:
                val, pos = read_varint(data, pos)
            except (ValueError, IndexError):
                break
            yield field_num, 0, val
        elif wire_type == 1:
            if pos + 8 > len(data):
                break
            val = struct.unpack_from('<Q', data, pos)[0]
            pos += 8
            yield field_num, 1, val
        elif wire_type == 2:
            try:
                length, pos = read_varint(data, pos)
            except (ValueError, IndexError):
                break
            if pos + length > len(data):
                break
            val = data[pos:pos+length]
            pos += length
            yield field_num, 2, val
        elif wire_type == 5:
            if pos + 4 > len(data):
                break
            val = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            yield field_num, 5, val
        else:
            break  # unknown wire type, stop


def scan_lri_blocks(lri_path: str) -> list[dict]:
    """Walk LELR blocks. Header layout (32 bytes):
      [0:4]   magic "LELR"
      [4:12]  total_block_len (u64 LE)
      [12:20] msg_offset (u64 LE)  — offset from block start to proto payload
      [20:24] msg_len (u32 LE)
      [24]    msg_type (u8)
    The protobuf lives at block_offset + msg_offset, NOT at byte 32.
    """
    blocks = []
    file_size = Path(lri_path).stat().st_size
    with open(lri_path, 'rb') as f:
        blk_offset = 0
        idx = 0
        while blk_offset < file_size:
            f.seek(blk_offset)
            hdr = f.read(32)
            if len(hdr) < 32 or hdr[0:4] != b'LELR':
                break
            total_len  = struct.unpack_from('<Q', hdr, 4)[0]
            msg_offset = struct.unpack_from('<Q', hdr, 12)[0]
            msg_len    = struct.unpack_from('<I', hdr, 20)[0]
            msg_type   = hdr[24]
            if total_len == 0:
                break
            # Read proto payload
            f.seek(blk_offset + msg_offset)
            payload = f.read(msg_len)
            blocks.append({
                'idx': idx,
                'block_offset': blk_offset,
                'total_size': total_len,
                'msg_offset': msg_offset,
                'payload_size': msg_len,
                'payload': payload,
                'msg_type': msg_type,
            })
            blk_offset += total_len
            idx += 1
    return blocks


# ── Proto field name map ───────────────────────────────────────────────────────

def load_field_map(strings_file: Path, cache_path: Path, rebuild: bool = False) -> dict:
    """Load field name map from cache or rebuild from libcp_strings_scratch.txt."""
    # Start with builtin map
    field_map = {f"{k[0]}.{k[1]}": v for k, v in BUILTIN_FIELD_MAP.items()}

    if not rebuild and cache_path.exists():
        try:
            with open(cache_path) as f:
                cached = json.load(f)
            # Merge cached (builtin takes precedence)
            for key, val in cached.items():
                if key not in field_map:
                    field_map[key] = val
            return field_map
        except Exception:
            pass

    # Try to parse strings file for additional proto declarations
    extra = {}
    if strings_file.exists():
        try:
            extra = _parse_strings_file(strings_file)
        except Exception as e:
            print(f"[WARN] Could not parse strings file: {e}", file=sys.stderr)

    merged = {**extra, **field_map}  # builtin overrides strings-derived
    try:
        with open(cache_path, 'w') as f:
            json.dump(merged, f, indent=2)
    except Exception:
        pass
    return merged


def _parse_strings_file(strings_file: Path) -> dict:
    """Extract proto field declarations from libcp_strings_scratch.txt.
    Look for patterns like field_name_data, _pb_field_, or descriptors near proto class names.
    Returns {class_name.field_num: [name, wire_type, sub_type]} dict.
    """
    extra = {}
    # Pattern: class name followed by field descriptors
    # e.g. "LightHeader.image_focal_length" near field numbers
    RE_CLASS = re.compile(r'\b(LightHeader|CameraModule|HwInfo|IMUData|SensorData|AWBData|DepthConfig)\b')
    RE_FIELD_LINE = re.compile(r'(\w+)\s+field\s*[=:]\s*(\d+)')

    current_class = None
    with open(strings_file, errors='replace') as f:
        for line in f:
            m_cls = RE_CLASS.search(line)
            if m_cls:
                current_class = m_cls.group(1)
            if current_class:
                m_fld = RE_FIELD_LINE.search(line)
                if m_fld:
                    name = m_fld.group(1)
                    num = int(m_fld.group(2))
                    key = f"{current_class}.{num}"
                    if key not in extra:
                        extra[key] = [name, "unknown", None]
    return extra


# ── Tree rendering ──────────────────────────────────────────────────────────────

WIRE_TYPE_NAMES = {0: "varint", 1: "fixed64", 2: "bytes/sub-msg", 5: "fixed32"}

def format_value(wire_type: int, raw_value, field_name: str, type_hint: str) -> str:
    """Format a raw proto value for display."""
    if wire_type == 2:
        if isinstance(raw_value, bytes):
            # Try to decode as UTF-8 string
            try:
                s = raw_value.decode('utf-8')
                if all(0x20 <= ord(c) < 0x7f or c in '\t\n\r' for c in s):
                    return repr(s)
            except Exception:
                pass
            return f"<{len(raw_value)} bytes>"
    elif wire_type == 0:
        if type_hint == "sint32":
            decoded = (raw_value >> 1) ^ -(raw_value & 1)
            return f"{decoded} (zigzag raw={raw_value})"
        return str(raw_value)
    elif wire_type == 5:
        # 32-bit: could be float or uint32
        float_val = struct.unpack('<f', struct.pack('<I', raw_value))[0]
        if 0.001 < abs(float_val) < 1e6 and not (float_val != float_val):
            return f"{raw_value} (float≈{float_val:.6g})"
        return str(raw_value)
    elif wire_type == 1:
        # 64-bit: could be double or uint64
        double_val = struct.unpack('<d', struct.pack('<Q', raw_value))[0]
        if 0.001 < abs(double_val) < 1e15 and not (double_val != double_val):
            return f"{raw_value} (double≈{double_val:.6g})"
        return str(raw_value)
    return str(raw_value)


def decode_block(payload: bytes, proto_class: str, field_map: dict,
                 depth: int = 2, indent: int = 0, focus_field: int = None,
                 output_json: bool = False) -> list:
    prefix = "  " * indent
    lines = []
    json_obj = {}

    # Group repeated fields
    from collections import defaultdict
    field_groups = defaultdict(list)

    for field_num, wire_type, raw_value in parse_proto_fields(payload):
        if focus_field is not None and field_num != focus_field:
            continue
        field_groups[field_num].append((wire_type, raw_value))

    for field_num in sorted(field_groups.keys()):
        entries = field_groups[field_num]
        map_key = f"{proto_class}.{field_num}"
        info = field_map.get(map_key)

        if info:
            name, type_str, sub_class = info[0], info[1], info[2]
            label = f"[{field_num}] {name} ({type_str})"
        else:
            wire_type0 = entries[0][0]
            label = f"[{field_num}] UNKNOWN_FIELD (wire_type={wire_type0})"
            sub_class = None
            type_str = WIRE_TYPE_NAMES.get(wire_type0, f"wt{wire_type0}")

        is_repeated = len(entries) > 1 or (info and "repeated" in (info[1] if info else ""))
        is_submsg = sub_class is not None

        if is_submsg and entries[0][0] == 2:
            count = len(entries)
            if is_repeated:
                lines.append(f"{prefix}{label} = {count} entries")
                if output_json:
                    json_obj[f"{field_num}_{name if info else 'unknown'}"] = []
                for i, (wt, rv) in enumerate(entries):
                    if depth > 0 and isinstance(rv, bytes):
                        lines.append(f"{prefix}  {sub_class}[{i}]:")
                        sub_lines = decode_block(
                            rv, sub_class, field_map,
                            depth=depth-1, indent=indent+2,
                            output_json=output_json
                        )
                        lines.extend(sub_lines)
            else:
                rv = entries[0][1]
                size = len(rv) if isinstance(rv, bytes) else 0
                lines.append(f"{prefix}{label} ({size} bytes)")
                if depth > 0 and isinstance(rv, bytes):
                    lines.append(f"{prefix}  {sub_class}:")
                    sub_lines = decode_block(
                        rv, sub_class, field_map,
                        depth=depth-1, indent=indent+2,
                        output_json=output_json
                    )
                    lines.extend(sub_lines)
        else:
            for wt, rv in entries:
                val_str = format_value(wt, rv, name if info else "?", type_str)
                lines.append(f"{prefix}{label} = {val_str}")
                if output_json:
                    key = f"{field_num}_{info[0] if info else 'unknown'}"
                    json_obj[key] = val_str

    return lines


def main():
    parser = argparse.ArgumentParser(description="LRI Proto Field Decoder")
    parser.add_argument("--lri", required=True, help="Path to LRI file")
    parser.add_argument("--block-index", type=int, default=0,
                        help="Block index (0 = LightHeader)")
    parser.add_argument("--proto-class", default="LightHeader",
                        help="Proto class name for field annotation")
    parser.add_argument("--depth", type=int, default=2,
                        help="Sub-message recursion depth")
    parser.add_argument("--field", type=int, default=None,
                        help="Focus only on this field number")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON instead of text tree")
    parser.add_argument("--rebuild-map", action="store_true",
                        help="Rebuild proto field map from strings file")
    parser.add_argument("--list-blocks", action="store_true",
                        help="List all blocks in the LRI without decoding")
    args = parser.parse_args()

    lri_path = Path(args.lri)
    if not lri_path.exists():
        print(f"[ERROR] LRI not found: {lri_path}", file=sys.stderr)
        sys.exit(1)

    # Load blocks
    blocks = scan_lri_blocks(str(lri_path))
    if not blocks:
        print("[ERROR] No LELR blocks found in LRI", file=sys.stderr)
        sys.exit(1)

    if args.list_blocks:
        print(f"{'Idx':>4}  {'PayloadBytes':>12}  {'TotalBytes':>10}")
        print("-" * 32)
        for b in blocks:
            print(f"{b['idx']:>4}  {b['payload_size']:>12}  {b['total_size']:>10}")
        return

    if args.block_index >= len(blocks):
        print(f"[ERROR] block-index {args.block_index} out of range (LRI has {len(blocks)} blocks)",
              file=sys.stderr)
        sys.exit(1)

    block = blocks[args.block_index]
    payload = block['payload']

    # Load field map
    field_map = load_field_map(STRINGS_FILE, FIELD_MAP_CACHE, rebuild=args.rebuild_map)

    # Decode
    focus = args.field
    lines = decode_block(
        payload, args.proto_class, field_map,
        depth=args.depth, indent=0,
        focus_field=focus,
        output_json=args.json
    )

    if args.json:
        # Re-run as JSON (simplified)
        print(json.dumps({"block_index": args.block_index,
                          "proto_class": args.proto_class,
                          "payload_bytes": len(payload),
                          "fields": lines}, indent=2))
    else:
        print(f"{args.proto_class}:  (block {args.block_index}, {len(payload)} bytes)")
        for line in lines:
            print(line)


if __name__ == "__main__":
    main()
