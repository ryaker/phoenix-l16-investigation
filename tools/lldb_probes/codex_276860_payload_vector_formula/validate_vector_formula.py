#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/codex_276860_payload_vector_formula")
TIERS = ("28mm", "35mm", "70mm", "150mm")
REQUIRED_TARGET_COUNTS = {
    "caller_pre_29a140": 1,
    "maker_after_299fd0": 1,
    "later_299c70_entry": 1,
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def words(hex_string):
    data = bytes.fromhex(hex_string)
    require(len(data) == 16, f"expected 16 bytes, got {len(data)}")
    return [data[i] | (data[i + 1] << 8) for i in range(0, 16, 2)]


def hex_from_words(values):
    out = bytearray()
    for value in values:
        out.append(value & 0xFF)
        out.append((value >> 8) & 0xFF)
    return bytes(out).hex()


def broadcast_hex(value):
    return hex_from_words([value & 0xFFFF] * 8)


def paddusw(a, b):
    return [min(0xFFFF, x + y) for x, y in zip(a, b)]


def psubusw(a, b):
    return [max(0, x - y) for x, y in zip(a, b)]


def pminuw(a, b):
    return [min(x, y) for x, y in zip(a, b)]


def psrld_16_as_words(values):
    out = []
    for i in range(0, 8, 2):
        out.extend([values[i + 1], 0])
    return out


def pslldq_2_as_words(values):
    return [0] + values[:7]


def expected_increment(src0, src6, accum, xmm1, xmm2, xmm3):
    shifted_src6 = pslldq_2_as_words(src6)
    shifted_src0 = psrld_16_as_words(src0)
    blend = [shifted_src0[0]] + shifted_src6[1:]
    v0 = pminuw(paddusw(src0, xmm1), blend)
    v6 = pminuw(paddusw(src6, xmm1), v0)
    v6 = pminuw(v6, xmm3)
    return psubusw(paddusw(accum, v6), xmm2), v6


def maker_sample(packet):
    for sample in packet.get("setup_samples", []):
        if sample.get("site") == "maker_after_299fd0":
            return sample
    return None


def validate_origin_context(path, packet, sample, index):
    origin = sample["vector_context"].get("origin_context")
    require(origin, f"{path.name}: sample {index} missing origin context")
    relationships = origin.get("relationships", {})
    for key in (
        "object_eq_target_object",
        "stack_minus_0x200_eq_object_0x168",
        "stack_minus_0x210_eq_object_0x198",
        "r10_eq_stack_minus_0x2e0",
        "r9_eq_object_record_base_plus_record_offset_plus_8",
        "watch_addr_eq_r9_plus_2rdx",
    ):
        require(
            relationships.get(key) is True,
            f"{path.name}: sample {index} origin relationship {key}={relationships.get(key)}",
        )

    require(
        origin.get("object_from_stack_rbp_minus_0x1c8") == packet.get("target_object"),
        f"{path.name}: sample {index} object stack target mismatch",
    )
    obj = origin.get("object_fields", {})
    require(obj.get("read_ok"), f"{path.name}: sample {index} object fields unreadable")
    qwords = obj.get("qwords", {})
    dwords = obj.get("dwords", {})
    maker = maker_sample(packet)
    require(maker, f"{path.name}: missing maker_after_299fd0 sample")
    output_local = maker.get("output_local", {})
    output_header = output_local.get("header_qwords_0x08_0x20") or []
    output_desc = output_local.get("descriptor_0x20") or {}
    require(len(output_header) >= 2, f"{path.name}: maker output header incomplete")
    require(
        qwords.get("0x108") == output_header[1],
        f"{path.name}: sample {index} object+0x108 != output record base",
    )
    require(
        qwords.get("0x138") == output_desc.get("aux_0x28"),
        f"{path.name}: sample {index} object+0x138 != output offset table",
    )
    require(
        dwords.get("0x130") == output_desc.get("stride_0x18"),
        f"{path.name}: sample {index} object+0x130 stride mismatch",
    )
    require(
        sample["vector_context"]["xmm_hex"].get("xmm1")
        == broadcast_hex(obj.get("u16_0x56")),
        f"{path.name}: sample {index} xmm1 not broadcast object+0x56",
    )


def validate_report(path):
    packet = json.loads(path.read_text())
    process = packet.get("process", {})
    require(process.get("state") == "exited", f"{path.name}: process did not exit")
    require(process.get("exit_status") == 0, f"{path.name}: nonzero exit {process}")
    require(not packet.get("drive_hit_step_cap"), f"{path.name}: hit step cap")
    require(not packet.get("errors"), f"{path.name}: errors {packet.get('errors')}")
    for site, expected in REQUIRED_TARGET_COUNTS.items():
        got = packet.get("target_counts", {}).get(site)
        require(got == expected, f"{path.name}: target count {site}={got}")

    samples = packet.get("watchpoint_samples", [])
    require(samples, f"{path.name}: no watchpoint samples")
    for index, sample in enumerate(samples):
        require(
            sample.get("libcp_va") == 0x277A16,
            f"{path.name}: sample {index} pc {sample.get('libcp_va')}",
        )
        disamb = sample.get("store_address_disambiguation", {})
        require(
            disamb.get("matches_r9_16byte_store"),
            f"{path.name}: sample {index} not r9 store {disamb}",
        )
        require(
            not disamb.get("matches_rcx_16byte_store"),
            f"{path.name}: sample {index} rcx ambiguity {disamb}",
        )

        ctx = sample["vector_context"]
        mem = ctx["memory16_hex"]
        xmm = ctx["xmm_hex"]
        for key in (
            "src0_rsi_plus_2rax",
            "src6_rdi_plus_2rdx",
            "accum_r10_plus_2rdx",
            "side_rcx_plus_2rdx",
            "payload_r9_plus_2rdx",
        ):
            require(mem.get(key), f"{path.name}: sample {index} missing {key}")
        for reg in ("xmm0", "xmm1", "xmm2", "xmm3", "xmm5", "xmm6"):
            require(xmm.get(reg), f"{path.name}: sample {index} missing {reg}")
        require(
            ctx.get("payload16_before_hit_hex"),
            f"{path.name}: sample {index} missing previous payload",
        )

        src0 = words(mem["src0_rsi_plus_2rax"])
        src6 = words(mem["src6_rdi_plus_2rdx"])
        accum = words(mem["accum_r10_plus_2rdx"])
        prev_payload = words(ctx["payload16_before_hit_hex"])
        got_xmm0 = words(xmm["xmm0"])
        got_xmm5 = words(xmm["xmm5"])
        got_xmm6 = words(xmm["xmm6"])
        exp_xmm0, exp_xmm6 = expected_increment(
            src0,
            src6,
            accum,
            words(xmm["xmm1"]),
            words(xmm["xmm2"]),
            words(xmm["xmm3"]),
        )
        exp_payload = paddusw(prev_payload, exp_xmm0)

        require(
            got_xmm0 == exp_xmm0,
            f"{path.name}: sample {index} xmm0 mismatch got={got_xmm0} exp={exp_xmm0}",
        )
        require(
            got_xmm6 == exp_xmm6,
            f"{path.name}: sample {index} xmm6 mismatch got={got_xmm6} exp={exp_xmm6}",
        )
        require(
            mem["side_rcx_plus_2rdx"] == hex_from_words(exp_xmm0),
            f"{path.name}: sample {index} side store mismatch",
        )
        require(
            mem["payload_r9_plus_2rdx"] == xmm["xmm5"],
            f"{path.name}: sample {index} full payload memory != xmm5",
        )
        validate_origin_context(path, packet, sample, index)
        if disamb.get("watch_minus_r9_plus_2rdx") == 0:
            require(
                got_xmm5[:4] == exp_payload[:4],
                f"{path.name}: sample {index} watched-lane payload mismatch "
                f"got={got_xmm5[:4]} exp={exp_payload[:4]}",
            )
    return packet


def main():
    for tier in TIERS:
        path = ROOT / f"vector_formula_{tier}.json"
        require(path.exists(), f"missing report {path}")
        packet = validate_report(path)
        hits = packet.get("watchpoint_hit_counts", {})
        print(
            f"{path.name}: OK samples={len(packet.get('watchpoint_samples', []))} "
            f"watch_hits={hits} vector_formula=0x2779b0..0x277a10"
        )


if __name__ == "__main__":
    main()
