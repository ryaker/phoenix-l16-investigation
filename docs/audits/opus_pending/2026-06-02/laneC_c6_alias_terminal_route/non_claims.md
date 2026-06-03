# non_claims — Lane C C6 alias/terminal-route (STATIC)

Explicit statements of what this packet does **NOT** establish. Weak-language discipline.

1. **NOT a runtime claim.** Everything here is static `otool` disassembly. "0 static literal-15 tests
   via the getter outside the clear" does NOT mean "never fires at runtime." No render or breakpoint
   was performed (forbidden for this agent).

2. **NOT a proof that the +0x30 clear is fully effective.** I confirmed two selection paths
   (0x1a8df0 family) ARE +0x30-gated and skip a cleared item. I did NOT audit guard-domination for all
   58 `f2720` callers; an un-guarded image-effecting consumer may exist outside the regions I read.

3. **NOT a C6-item attribution for the +0x68..0xa0 blind read list.** The 145-entry
   `angle1_blind_0x68_0xa0_reads.log` is a binary-wide superset across unrelated struct types. The
   0xe7634..0xe76a4 getter cluster (incl. `leaq 0x78`) is a DIFFERENT, larger parent container, not the
   C6 item. Do NOT cite any 0x68..0xa0 read as a C6-item alias without rdi-provenance proof.

4. **NOT a claim that key 15 -> group-type 2 has an image effect.** I established the classifier
   `0xf6c60` maps key 15 to camera-group-type 2 and is +0x30-blind. I did NOT trace group-type-2
   forward to any pixel/merge/kernel operation. "Classification survives the clear" != "the cleared
   item still contributes to the output image."

5. **NOT a found alternate route.** No `call 0xf2720`-independent path carrying a key-15-derived
   pointer into an image kernel was confirmed. Result stands as "no static alternate route found under
   this search," not "no alternate route exists."

6. **NOT a constructor-completeness guarantee for item lifetime.** I listed the fields the constructor
   `0xf2770` writes. Other code may write +0x68..0xa0 on the same object later (post-construction
   mutation); I did not exhaustively prove those offsets stay unwritten across the object's lifetime.

7. **anchorPassed asterisk.** 0x3eced0 is the enclosing function prologue; the mulps/maxps/sqrtps
   triple is at 0x3ecfe4+ inside it. Treated as PASS at function granularity; flagged for Codex to
   confirm the briefing intended the function entry rather than a literal instruction VA.

8. **No symbol names.** No RTTI / demangled type name for the C6 item struct was resolved; "C6 item",
   "key", "active flag", "camera-group-type" are descriptive labels inferred from disasm shape, not
   confirmed from symbols.
