.text
.globl _range_hook_shim
.p2align 4, 0x90
_range_hook_shim:
    movq %r12, %rdx
    movq %r14, %rcx
    movq %rbp, %r8
    jmp _range_hook_c

.globl _post_overlay_hook_shim
.p2align 4, 0x90
_post_overlay_hook_shim:
    movq %r12, %rdi
    movq %rbp, %rsi
    jmp _post_overlay_hook_c
