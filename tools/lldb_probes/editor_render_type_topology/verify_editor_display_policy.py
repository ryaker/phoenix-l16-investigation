#!/usr/bin/env python3
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LUMEN = Path("/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/MacOS/Lumen")
RUN = ROOT / "runs/editor_render_type_topology"
ACRE_REPLAY = ROOT / "tools/lldb_probes/editor_render_type_topology/run_acre_replay.sh"
ACRE_COLOR_DUMP = ROOT / "tools/lldb_probes/editor_render_type_topology/run_acre_color_dump.sh"
ACRE_CONVERTER_REPLAY = ROOT / "tools/lldb_probes/editor_render_type_topology/run_acre_converter_replay.sh"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_bytes(blob, offset, expected, label):
    actual = blob[offset : offset + len(expected)]
    assert actual == expected, (
        f"{label}: {offset:#x}: expected {expected.hex()}, got {actual.hex()}"
    )


def u32(blob, offset):
    return struct.unpack_from("<I", blob, offset)[0]


def u64(blob, offset):
    return struct.unpack_from("<Q", blob, offset)[0]


def cstring(blob, offset):
    return blob[offset : blob.index(b"\0", offset)].decode("ascii")


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def rel32_target(blob, callsite):
    assert blob[callsite] == 0xE8, hex(callsite)
    return callsite + 5 + struct.unpack_from("<i", blob, callsite + 1)[0]


def main():
    libcp = LIBCP.read_bytes()
    lumen = LUMEN.read_bytes()

    assert sha256(LIBCP) == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
    assert sha256(LUMEN) == "1cd727486f9b21c4eacab4a99cff4a85f3c1c3f5e4f3a78b76617ec12438065d"

    require_bytes(libcp, 0x5A8890, struct.pack("<4f", 255.0, 255.0, 255.0, 255.0), "scale")
    require_bytes(
        libcp,
        0x27E1B0,
        bytes.fromhex("0f2850f00f59d1660f5bd2660f6bd0660f67d0"),
        "RGBA vector pack",
    )
    require_bytes(
        libcp,
        0x3BDA06,
        bytes.fromhex("be0a0000004c89ffe83d8a000083f801"),
        "ParamInt(10) dispatch",
    )
    require_bytes(
        libcp,
        0x3BDA2B,
        bytes.fromhex("660f6f055dae1e00660f7f8540fdffff"),
        "RGBA 255-vector load",
    )
    require_bytes(
        libcp,
        0x3BDB30,
        bytes.fromhex("0f28070f59c20fc6c0c6660f5bc0660f6bc1660f67c1"),
        "BGRA lane swap and pack",
    )

    # The live display update is record type 13. Type 4 is the separate
    # public Renderer::serialize route and is not produced by this harness.
    require_bytes(libcp, 0x3BF85E, bytes.fromhex("c78560ffffff0d000000"), "type-13 tag")
    require_bytes(libcp, 0x3BF868, bytes.fromhex("c78564ffffff02000000"), "type-13 priority")
    assert rel32_target(libcp, 0x3BF8BC) == 0x3BFC40
    assert rel32_target(libcp, 0x3903F8) == 0x3B6CA0
    require_bytes(libcp, 0x3B6D20, bytes.fromhex("48c78560ffffff04000000"), "type-4 serialize tag")
    assert rel32_target(libcp, 0x3B6D6E) == 0x3BFC40

    render_worker_type = cstring(libcp, u64(libcp, u64(libcp, 0x65EA80) + 8))
    assert "RendererPrivateC1EN5CIAPI15RendererProfileEE3$_2" in render_worker_type
    assert u64(libcp, 0x65EAB8) == 0x3BB2B0
    request_type = cstring(libcp, u64(libcp, u64(libcp, 0x65EE00) + 8))
    assert "RendererPrivate16requestRenderROI" in request_type
    assert "E4$_12" in request_type
    assert u64(libcp, 0x65EE38) == 0x3BF820

    pipeline_cache_type = cstring(libcp, u64(libcp, u64(libcp, 0x65F5D8) + 8))
    dof_cache_type = cstring(libcp, u64(libcp, u64(libcp, 0x65F868) + 8))
    assert "lt13PipelineCacheC1" in pipeline_cache_type
    assert "TileINS2_4Vec3INS2_7Float16" in pipeline_cache_type
    assert "lt8DOFCacheC1" in dof_cache_type
    assert "INS2_10DepthCache" in dof_cache_type
    assert u64(libcp, 0x65F610) == 0x3EC960
    assert u64(libcp, 0x65F8A0) == 0x3F0B90

    require_bytes(libcp, 0x3BB4F2, bytes.fromhex("418b8674070000"), "rendering-mode load")
    assert rel32_target(libcp, 0x3BB531) == 0x3C6F80
    require_bytes(libcp, 0x3BB546, bytes.fromhex("498bbeb8060000"), "DOFCache threshold object")
    assert rel32_target(libcp, 0x3BB54D) == 0x3F06D0
    require_bytes(libcp, 0x3BB55A, bytes.fromhex("0f2ec80f839f020000"), "mode-0 cache compare")
    require_bytes(libcp, 0x3BB563, bytes.fromhex("498bbeb8060000"), "mode-0 DOFCache arm")
    require_bytes(libcp, 0x3BB802, bytes.fromhex("498bbe88060000"), "mode-0 PipelineCache arm")
    assert rel32_target(libcp, 0x3BB81D) == 0x3D0650
    require_bytes(libcp, 0x3BB822, bytes.fromhex("498b8670080000"), "per-level pipeline vector")
    assert rel32_target(libcp, 0x3BB867) == 0x31B110

    require_bytes(
        lumen,
        0x20018,
        bytes.fromhex("81fae18000000f94c00fb6d0be0a000000"),
        "GL_BGRA to ParamInt(10)",
    )
    require_bytes(
        lumen,
        0x3A16D,
        bytes.fromhex("b808190000b9e18000000f45c8"),
        "fail-safe GL_RGBA/GL_BGRA selection",
    )
    require_bytes(
        lumen,
        0x6D771,
        bytes.fromhex("8b452889442408891c2448c744241800000000c744241001140000"),
        "texture upload format and GL_UNSIGNED_BYTE",
    )

    indirect = subprocess.check_output(["otool", "-Iv", str(LUMEN)], text=True)
    assert (
        "0x000000010016e5d2  9297 "
        "__ZN5CIAPI12RendererBase11setPropertyENS_8ParamIntEi"
    ) in indirect

    packet = json.loads((RUN / "output_write_watch_level4_28mm.json").read_text())
    assert packet["errors"] == []
    assert packet["process"]["exit_status"] == 0
    assert packet["target"]["level"] == 4
    assert packet["write"]["pc_file_address"] == 0x27E1CD
    assert packet["write"]["scale_f32"] == [255.0] * 4
    assert packet["write"]["mxcsr"] & 0x6000 == 0
    expected = bytes(
        max(0, min(255, round(value * 255.0)))
        for value in packet["write"]["source_f32"]
    )
    assert packet["write"]["after_hex"] == expected.hex()
    assert packet["write"]["packed_xmm2_hex"][:8] == expected.hex()

    parent_record = packet["write"]["parent_record"]
    assert parent_record["type_u32_0x00"] == 13
    assert parent_record["priority_u32_0x04"] == 2
    renderer = packet["write"]["parent_renderer"]
    assert renderer["rendering_mode_u32_0x774"] == 0
    assert renderer["depth_ready_i32_0x888"] == 0
    assert renderer["mode0_request_scale_f32_owner_0x48"] == renderer[
        "mode0_dof_threshold_f32_cache_0x6b8_0x98"
    ]
    base = renderer["libcp_load_address"]
    render_object = bytes.fromhex(renderer["render_function_object_hex"])
    assert struct.unpack_from("<Q", render_object, 0)[0] - base == 0x65EA88
    cache_688 = bytes.fromhex(renderer["cache_0x688"]["raw_hex"])
    cache_6b8 = bytes.fromhex(renderer["cache_0x6b8"]["raw_hex"])
    assert struct.unpack_from("<II", cache_688, 0) == (512, 512)
    assert struct.unpack_from("<II", cache_6b8, 0) == (512, 512)
    assert struct.unpack_from("<Q", cache_688, 0x50)[0] - base == 0x65F5E0
    assert struct.unpack_from("<Q", cache_6b8, 0x50)[0] - base == 0x65F870
    adapters = renderer["level_adapters_0x870"]
    assert adapters["count"] == 5
    assert len(adapters["entries"]) == 5
    active_adapter = bytes.fromhex(adapters["entries"][4]["raw_hex"])
    assert struct.unpack_from("<I", active_adapter, 0x18)[0] == 4
    assert active_adapter[0x58] == 0

    source_path = RUN / "type1_28mm_level4_source_f32.raw"
    raw_path = RUN / "type1_28mm_level4_watch.raw"
    export_source_path = RUN / "export_type2_28mm_652_source_f32.raw"
    pipeline_before_path = RUN / "display_pipeline_tile_before.raw"
    pipeline_after_path = RUN / "display_pipeline_tile_after.raw"
    source = source_path.read_bytes()
    raw = raw_path.read_bytes()
    export_source = export_source_path.read_bytes()
    pipeline_before = pipeline_before_path.read_bytes()
    pipeline_after = pipeline_after_path.read_bytes()
    assert len(source) == 652 * 489 * 16
    assert len(raw) == 652 * 489 * 4
    assert len(export_source) == len(source)
    assert pipeline_before == export_source
    assert pipeline_after == source
    assert raw[3::4] == b"\xff" * (652 * 489)
    replay = bytearray()
    for pixel in struct.iter_unpack("<4f", source):
        assert pixel[3] == 1.0
        for value in pixel:
            scaled = struct.unpack("<f", struct.pack("<f", value * 255.0))[0]
            replay.append(max(0, min(255, round(scaled))))
    assert bytes(replay) == raw
    center = (244 * 652 + 326) * 4
    assert raw[center : center + 4].hex() == expected.hex()

    export_packet = json.loads((RUN / "export_float_input_28mm_652.json").read_text())
    assert export_packet["errors"] == []
    assert export_packet["process"]["exit_status"] == 0
    assert export_packet["hits"] == 1
    assert export_packet["capture"]["pc_file_address"] == 0x41E599
    assert export_packet["capture"]["width"] == 652
    assert export_packet["capture"]["height"] == 489
    assert export_packet["capture"]["stride_pixels"] == 652
    assert export_packet["capture"]["sha256"] == sha256(export_source_path)

    tile_packet = json.loads((RUN / "display_pipeline_tile_28mm.json").read_text())
    assert tile_packet["errors"] == []
    assert tile_packet["process"]["exit_status"] == 0
    assert tile_packet["before"]["pc_file_address"] == 0x3BB867
    assert tile_packet["after"]["pc_file_address"] == 0x3BB86C
    assert tile_packet["before"]["descriptor"]["sha256"] == sha256(export_source_path)
    assert tile_packet["after"]["descriptor"]["sha256"] == sha256(source_path)

    stages_packet = json.loads((RUN / "display_pipeline_stages_28mm.json").read_text())
    assert stages_packet["errors"] == []
    assert stages_packet["process"]["exit_status"] == 0
    assert stages_packet["return_pc_file_address"] == 0x3BB86C
    expected_stages = [
        (3, 0x65B148, 0x340F70, "PipelineC1EvE3$_6", "5215ffcac45708993f03776ce3a5733b9ee575574e1fde43fb6308ea4c25bc40"),
        (10, 0x65D038, 0x347680, "setColorCorrection", "b31fb9f69c40b73d94bc5aade11411f644d61ce7fbc1b7e4c1c8aa9386115927"),
        (11, 0x65B1C8, 0x341040, "PipelineC1EvE3$_7", "185acdad81e4a7870b8dcc058704d6ec3ab50b88b61688394c919f986f9235e3"),
        (12, 0x65CB08, 0x346110, "setLensShading", "185acdad81e4a7870b8dcc058704d6ec3ab50b88b61688394c919f986f9235e3"),
        (13, 0x65D6B8, 0x3496E0, "setToneAdjust", "b738cd642eecdff67545dd20721c85da75968105e1812a58a7e7d2bee05bed77"),
        (14, 0x65D818, 0x349E80, "setContrastAdjust", "b738cd642eecdff67545dd20721c85da75968105e1812a58a7e7d2bee05bed77"),
        (15, 0x65DC58, 0x34AD50, "setToneMapping", "f8acda7264f7b7e458bbbe6acd69fe38ea172771fa938b65f0cffb5ebf1bc860"),
    ]
    actual_stages = [
        (
            event["pipeline_vector_index_r15"],
            event["vtable_file_address"],
            event["target_file_address"],
        )
        for event in stages_packet["events"]
    ]
    assert actual_stages == [row[:3] for row in expected_stages]
    for event, (_, vtable, _, identity, expected_sha) in zip(
        stages_packet["events"], expected_stages
    ):
        type_name = cstring(libcp, u64(libcp, u64(libcp, vtable - 8) + 8))
        assert identity in type_name
        after_image = event["after_image"]
        assert (after_image["width"], after_image["height"]) == (652, 489)
        assert after_image["stride_pixels"] == 652
        assert after_image["sha256"] == expected_sha
        stage_path = Path(after_image["dump_path"])
        assert stage_path.resolve().is_relative_to(RUN.resolve())
        assert stage_path.stat().st_size == 652 * 489 * 16
        assert sha256(stage_path) == expected_sha

    # The tested default route has live lens/contrast callback records, but
    # both are byte-exact no-ops over the complete level-4 float image.
    assert expected_stages[2][4] == expected_stages[3][4]
    assert expected_stages[4][4] == expected_stages[5][4]
    assert expected_stages[-1][4] == sha256(source_path)

    owner_event = stages_packet["events"][2]
    pipeline_fields = bytes.fromhex(owner_event["pipeline_fields_0x1600_hex"])
    assert len(pipeline_fields) == 0x80
    assert struct.unpack_from("<f", pipeline_fields, 0x18)[0] == 1.0
    assert pipeline_fields[0x1C] == 1
    assert struct.unpack_from("<f", pipeline_fields, 0x60)[0] == 0.0
    assert struct.unpack_from("<Q", pipeline_fields, 0x68)[0] == owner_event["tone_mapper"]
    assert owner_event["tone_mapper_vtable_file_address"] == 0x659B30

    tone_type = cstring(libcp, u64(libcp, u64(libcp, 0x659B28) + 8))
    tone_callback_type = cstring(libcp, u64(libcp, u64(libcp, 0x659B70) + 8))
    assert tone_type == "N2lt7TMO_ACRE"
    assert "2lt7TMO_ACR7process" in tone_callback_type
    assert u64(libcp, 0x659B40) == 0x2D7780
    assert u64(libcp, 0x659BA8) == 0x2D7A30
    assert hashlib.sha256(libcp[0x2D7780:0x2D7883]).hexdigest() == (
        "6a232e871b38348bbcebbdb647d54a27ee0ad23cf541948a8781fddfa9dc54b4"
    )
    assert hashlib.sha256(libcp[0x2D7A30:0x2D8080]).hexdigest() == (
        "f1fe1b218a4458908de9b7235700cc5f79d5d639ce05b618387d85098c9fd4ed"
    )
    assert hashlib.sha256(libcp[0xABF20:0xAC743]).hexdigest() == (
        "5baa62d37c000d0fe190419c30c3cb7075675c63143639a3d11e4b21355fcc9f"
    )
    require_bytes(
        libcp,
        0x5E3120,
        bytes.fromhex(
            "0bd723bb" * 4 + "4901c942" * 4 + "0bd7233b" * 4
            + "90c2f53b" * 4 + "0bd7a3bb" * 4 + "aaa4803f" * 4
            + "00008044"
        ),
        "ACRE toe/LUT constants",
    )
    assert cstring(libcp, 0x632C9C) == "srgb"
    require_bytes(
        libcp,
        0x32842C,
        bytes.fromhex("c78528fdffff02000000"),
        "public srgb selector 2",
    )

    acre_packet = json.loads((RUN / "acre_runtime_28mm.json").read_text())
    assert acre_packet["errors"] == []
    assert acre_packet["process_exit"]["exit_status"] == 0
    acre_process = acre_packet["process"]
    assert acre_process["tone_mapper_vtable_file_address"] == 0x659B30
    assert struct.pack("<f", acre_process["ev_offset_f32"]).hex() == "7e03803f"
    assert acre_process["lut_file_address"] == 0x5E41B4
    assert acre_process["lut_count"] == 1025
    assert acre_process["lut_sha256"] == (
        "0d5997a0708dec35863113bb4516dd056ed927dd75609e8c3a2c935953107de1"
    )

    # The editor request builder materializes the public tone-mapping
    # properties rather than taking the observed ACRE parameters from an
    # opaque object. Its default type string is the installed `light_v1`
    # singleton at 0x673e48, initialized directly from the public literal.
    assert cstring(libcp, 0x631BEC) == "tone_mapping.type"
    assert cstring(libcp, 0x634396) == "tone_mapping.ev_offset"
    assert cstring(libcp, 0x631BE7) == "none"
    assert cstring(libcp, 0x631CAF) == "default"
    assert cstring(libcp, 0x63376C) == "linear"
    assert cstring(libcp, 0x63307C) == "acr"
    assert cstring(libcp, 0x6330C1) == "light_v1"
    assert cstring(libcp, 0x6330CA) == "light_v1_lowlight"
    assert cstring(libcp, 0x6330DC) == "light_v2"
    require_bytes(
        libcp,
        0x436691,
        bytes.fromhex("488d1db0d72300488d3522ca1f00ba08000000"),
        "default tone type light_v1 singleton initialization",
    )
    require_bytes(
        libcp,
        0x42E17B,
        bytes.fromhex("488d356a3a2000"),
        "tone_mapping.type property key",
    )
    require_bytes(
        libcp,
        0x42E1B4,
        bytes.fromhex("488d358d5c2400"),
        "tone_mapping.type default light_v1 object",
    )

    # The installed tone-type schema maps light_v1 to enum 4. The enum-4
    # jump-table arm constructs TMO_ACRE with curve index 1, and the
    # constructor's four-pointer table maps index 1 to the observed LUT.
    require_bytes(
        libcp,
        0x325DDA,
        bytes.fromhex("488d1d7fae3400488d35d9d23000ba08000000"),
        "light_v1 enum-name singleton initialization",
    )
    require_bytes(
        libcp,
        0x328BC1,
        bytes.fromhex("4c8dad50ffffff488d3579803400"),
        "light_v1 enum-map name copy",
    )
    require_bytes(libcp, 0x328B40, bytes.fromhex("c78508ffffff00000000"), "none enum 0")
    require_bytes(libcp, 0x328B7A, bytes.fromhex("c78528ffffff01000000"), "default enum 1")
    require_bytes(libcp, 0x328BB7, bytes.fromhex("c78548ffffff02000000"), "linear enum 2")
    require_bytes(libcp, 0x328BDA, bytes.fromhex("c78568ffffff03000000"), "acr enum 3")
    require_bytes(
        libcp,
        0x328BFD,
        bytes.fromhex("c7458804000000"),
        "light_v1 enum value 4",
    )
    require_bytes(libcp, 0x328C1A, bytes.fromhex("c745a805000000"), "lowlight enum 5")
    require_bytes(libcp, 0x328C34, bytes.fromhex("c745c806000000"), "light_v2 enum 6")
    require_bytes(
        libcp,
        0x319347,
        bytes.fromhex("488d3d02833500488d75d04889c2e876b00000"),
        "tone type lookup through installed enum map",
    )
    require_bytes(
        libcp,
        0x339D38,
        bytes.fromhex("4489e84183fd060f87c72e0000488d0d18300000"),
        "tone type enum jump dispatch",
    )
    assert struct.unpack_from("<7i", libcp, 0x33CD64) == (
        -0x2F51,
        -0x300F,
        -0x300F,
        -0x2EE3,
        -0x2E23,
        -0x2D60,
        -0x2C9D,
    )
    require_bytes(
        libcp,
        0x339F41,
        bytes.fromhex("bf18000000e84dc421004989c7be010000004c89ffe855d7f9ff"),
        "enum-4 ACRE curve-index-1 construction",
    )
    assert struct.unpack_from("<4Q", libcp, 0x659C70) == (
        0x5E31B0,
        0x5E41B4,
        0x5E51B8,
        0x5E61BC,
    )

    # The request builder writes tone_mapping.ev_offset as log2f of the
    # already admitted capture-normalization helper. The property consumer
    # then writes that float into TMO base +0x08.
    require_bytes(
        libcp,
        0x42E1EA,
        bytes.fromhex("488d35a5612000"),
        "tone_mapping.ev_offset property key",
    )
    assert rel32_target(libcp, 0x42E227) == 0x3E0A20
    assert rel32_target(libcp, 0x42E22F) == 0xF3FC0
    assert rel32_target(libcp, 0x42E234) == 0x556002
    require_bytes(
        libcp,
        0x33EB20,
        bytes.fromhex("554889e5488bbf681600004885ff74065de97a81f9ff5dc3"),
        "tone EV setter forwarding to TMO object",
    )
    require_bytes(
        libcp,
        0x2D6CB0,
        bytes.fromhex("554889e5f30f1147085dc3"),
        "TMO EV field write at +0x08",
    )

    consumed = json.loads(
        (ROOT / "runs/lri_consumed_block_roles/unit1_28mm.json").read_text()
    )
    merged = consumed["merged_preferences"][0]
    captured = next(
        row for row in consumed["exposure_normalization"]
        if row.get("captured_image") is not None
    )
    image_time = merged["image_integration_time_ns"]["value"]
    image_gain = merged["image_gain"]["value"]
    sensor_time = captured["sensor_exposure"]
    sensor_gain = captured["sensor_analog_gain"]
    numerator = f32(f32(image_time) * f32(image_gain))
    denominator = f32(f32(sensor_time) * f32(sensor_gain))
    exposure_scale = f32(numerator / denominator)
    exposure_ev = f32(math.log2(exposure_scale))
    assert numerator == 22479080.0
    assert denominator == 11238709.0
    assert exposure_scale == 2.000147819519043
    assert struct.pack("<f", exposure_scale).hex() == "6c020040"
    assert exposure_ev == acre_process["ev_offset_f32"]
    assert struct.pack("<f", exposure_ev).hex() == "7e03803f"
    assert merged["ev_offset"] == {"present": True, "value": 0.0}
    assert consumed["counts"]["ev_offset_accessor"] == 0
    acre_lut_path = Path(acre_process["lut_path"])
    assert acre_lut_path.resolve().is_relative_to(RUN.resolve())
    assert acre_lut_path.read_bytes() == libcp[0x5E41B4:0x5E41B4 + 1025 * 4]
    assert acre_process["source"] == acre_process["destination"]
    assert acre_process["source"]["width"] == 652
    assert acre_process["source"]["height"] == 489
    assert acre_process["source"]["stride_pixels"] == 652
    expected_acre_color = (
        "7c2dd33e3714b73e9cc4383eedc6593e3714373f7dd0933d"
        "21629e3cef1af43d2147733fb41da03eb875a83e0700000002000000"
    )
    assert acre_process["color_space_raw_hex"] == expected_acre_color
    acre_worker = acre_packet["worker"]
    assert acre_worker["source"] == acre_process["source"]["address"]
    assert acre_worker["destination"] == acre_process["destination"]["address"]
    assert acre_worker["tone_mapper"] == acre_process["tone_mapper"]
    assert acre_worker["color_space"] == acre_process["color_space"]
    assert acre_worker["rectangle"] == [0, 0, 256, 256]
    intermediate = acre_packet["intermediate"]
    assert intermediate["pc_file_address"] == 0x2D7F60
    assert intermediate["sha256"] == (
        "ccb4b056be2b806f467c856d2dcb194673c99be1cbadc2dcae2d16c1b777380b"
    )
    assert intermediate["dump_size"] == 256 * 256 * 16

    subprocess.run(["bash", str(ACRE_REPLAY)], cwd=ROOT, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    acre_intermediate_path = Path(intermediate["dump_path"])
    acre_replay_path = RUN / "acre_intermediate_replay_256x256_f32.raw"
    assert acre_intermediate_path.read_bytes() == acre_replay_path.read_bytes()

    converter = acre_packet["converter"]
    assert converter["pc_file_address"] == 0xBF4A0
    assert converter["selected_function_file_address"] == 0xABF20
    assert converter["branch_pc_file_address"] == 0xAC600
    assert converter["source"] == converter["destination"]
    assert converter["source_config"] == acre_process["color_space"]
    assert converter["adaptation_hex"] == (
        "aea0743ff8bcbcbcf05b813d35bfe7bcc445813f3a18ac3c487e493c0ccca7bc7f3aaa3f"
    )
    assert converter["matrix_rows_hex"] == [
        "502e0240144e6abe48680cbc00000000",
        "94323abf57a99d3f2cf71cbe00000000",
        "460d9dbeb8293fbbb9b7943f00000000",
    ]
    post_conversion = acre_packet["post_conversion"]
    assert post_conversion["pc_file_address"] == 0x2D8018
    assert post_conversion["dump_size"] == 256 * 256 * 16
    assert post_conversion["sha256"] == (
        "da68813263016b0b3cd82bf202db74d5b58b209bf30cb1d5583260e892d36cbb"
    )
    subprocess.run(["bash", str(ACRE_CONVERTER_REPLAY)], cwd=ROOT, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    post_conversion_path = Path(post_conversion["dump_path"])
    converter_replay_path = RUN / "acre_post_conversion_replay_256x256_f32.raw"
    assert post_conversion_path.read_bytes() == converter_replay_path.read_bytes()

    color_output = subprocess.check_output(
        ["bash", str(ACRE_COLOR_DUMP)], cwd=ROOT, text=True
    )
    color_fields = dict(
        line.split("=", 1) for line in color_output.splitlines() if "=" in line
    )
    assert color_fields["converter_5_2"] == "0xabf20"
    assert color_fields["source_config"] == expected_acre_color
    assert color_fields["adaptation"] == (
        "aea0743ff8bcbcbcf05b813d35bfe7bcc445813f3a18ac3c487e493c0ccca7bc7f3aaa3f"
    )

    result = {
        "status": "PASS",
        "lumen_sha256": sha256(LUMEN),
        "libcp_sha256": sha256(LIBCP),
        "runtime_report": str(RUN / "output_write_watch_level4_28mm.json"),
        "runtime_source_f32": packet["write"]["source_f32"],
        "runtime_packed_hex": expected.hex(),
        "runtime_mxcsr": packet["write"]["mxcsr"],
        "runtime_record_type": parent_record["type_u32_0x00"],
        "runtime_record_priority": parent_record["priority_u32_0x04"],
        "runtime_render_worker": "lt::RendererPrivate::RendererPrivate(RendererProfile)::$_2 / 0x3bb2b0",
        "runtime_rendering_mode": renderer["rendering_mode_u32_0x774"],
        "runtime_selected_cache": "lt::PipelineCache at RendererPrivate+0x688",
        "runtime_mode0_request_scale": renderer["mode0_request_scale_f32_owner_0x48"],
        "runtime_mode0_dof_threshold": renderer[
            "mode0_dof_threshold_f32_cache_0x6b8_0x98"
        ],
        "runtime_level_pipeline_count": adapters["count"],
        "source_level4_sha256": sha256(source_path),
        "export_source_level4_sha256": sha256(export_source_path),
        "export_equals_pipeline_before": export_source == pipeline_before,
        "editor_equals_pipeline_after": source == pipeline_after,
        "display_pipeline_stages": [
            {
                "index": index,
                "vtable": hex(vtable),
                "target": hex(target),
                "identity": identity,
            }
            for index, vtable, target, identity, _ in expected_stages
        ],
        "display_pipeline_stage_sha256": [row[4] for row in expected_stages],
        "display_lens_stage_exact_noop": True,
        "display_contrast_stage_exact_noop": True,
        "display_lens_strength_f32": 1.0,
        "display_lens_enable_u8": 1,
        "display_contrast_f32": 0.0,
        "display_tone_mapper": "lt::TMO_ACRE / 0x2d7780 -> TMO_ACR::process::$_0 / 0x2d7a30",
        "display_acre_ev_offset_f32": acre_process["ev_offset_f32"],
        "display_acre_exposure_scale_f32": 2.000147819519043,
        "display_acre_ev_public_origin": (
            "log2f((ViewPreferences.image_integration_time_ns * "
            "ViewPreferences.image_gain) / "
            "(CameraModule.sensor_exposure * CameraModule.sensor_analog_gain))"
        ),
        "display_acre_type_public_origin": "tone_mapping.type=light_v1",
        "display_acre_type_enum": 4,
        "display_acre_curve_index": 1,
        "display_acre_lut_file_address": "0x5e41b4",
        "display_acre_lut_sha256": acre_process["lut_sha256"],
        "display_acre_replay_sha256": intermediate["sha256"],
        "display_acre_replay_bytes": intermediate["dump_size"],
        "display_acre_conversion_source_config": "linear_prophoto_rgb/D50 selector 5",
        "display_acre_output_config": "sRGB/D65 selector 2",
        "display_acre_color_converter": "0xabf20 matrix branch 0xac600",
        "display_acre_color_matrix_rows": converter["matrix_rows_f32"],
        "display_acre_post_conversion_sha256": post_conversion["sha256"],
        "display_acre_post_conversion_replay_bytes": post_conversion["dump_size"],
        "raw_level4_sha256": sha256(raw_path),
        "raw_level4_alpha_all_255": True,
        "full_level4_replay_bytes": len(raw),
        "full_level4_replay_exact": True,
        "pyramid": [
            [10432, 7824, 41728],
            [5216, 3912, 20864],
            [2608, 1956, 10432],
            [1304, 978, 5216],
            [652, 489, 2608],
        ],
        "normal_gui_gl_format": "GL_BGRA",
        "fallback_gui_gl_format": "GL_RGBA",
    }
    output = RUN / "editor_display_policy_verification.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
