setExitCode(1)

setStylusContract(
  1,
  (module
    (import "vm_hooks" "storage_load_bytes32" (func $storage_load_bytes32 (param i32 i32)))
    (import "vm_hooks" "read_args"            (func $read_args            (param i32)))
    (import "vm_hooks" "write_result"         (func $write_result         (param i32 i32)))

    (func (export "user_entrypoint") (param $args_len i32) (result i32)
        (call $read_args (i32.const 0))
        
        (call $storage_load_bytes32 (i32.const 0) (i32.const 32))

        (call $write_result (i32.const 32) (i32.const 32))

        (i32.const 0)
    )
    (memory (export "memory") 1 1)
  ),
  .Map ;; Map concatenation syntax doesn't work here
    [1 <- 100]
    [2 <- 200]
    [3 <- 300]
    [4 <- 400]
)

callStylus(0, 1, Int2Bytes(32, 1, BE), 0)
checkOutput(Int2Bytes(32, 100, BE))

callStylus(0, 1, Int2Bytes(32, 2, BE), 0)
checkOutput(Int2Bytes(32, 200, BE))

callStylus(0, 1, Int2Bytes(32, 3, BE), 0)
checkOutput(Int2Bytes(32, 300, BE))

callStylus(0, 1, Int2Bytes(32, 4, BE), 0)
checkOutput(Int2Bytes(32, 400, BE))

setExitCode(0)
