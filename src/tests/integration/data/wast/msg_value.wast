;; NOTE: The Wasm module(s) in this file is for testing Stylus host functions in isolation.
;; The module does not implement the EVM ABI and is not intended for deployment.

setExitCode(1)

setStylusContract(
  1,
  (module
    (import "vm_hooks" "msg_value" (func $msg_value (param i32)))
    (import "vm_hooks" "write_result"         (func $write_result         (param i32 i32)))

    (func (export "user_entrypoint") (param $args_len i32) (result i32)
        (call $msg_value (i32.const 0))
        (call $write_result (i32.const 0) (i32.const 32))
        (i32.const 0)
    )
    (memory (export "memory") 1 1)
  ),
  .Map
)

callStylus(0, 1, .Bytes, 0)
checkOutput(Int2Bytes(32, 0, BE))

callStylus(0, 1, .Bytes, 100000000)
checkOutput(Int2Bytes(32, 100000000, BE))

callStylus(0, 1, .Bytes, 100000000100000000)
checkOutput(Int2Bytes(32, 100000000100000000, BE))

setExitCode(0)
