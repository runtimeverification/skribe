setExitCode(1)

setStylusContract(
  1,
  (module
    (import "vm_hooks" "storage_load_bytes32"  (func $storage_load_bytes32 (param i32 i32)))
    (import "vm_hooks" "storage_cache_bytes32" (func $storage_cache_bytes32 (param i32 i32)))
    (import "vm_hooks" "read_args"             (func $read_args            (param i32)))
    (import "vm_hooks" "write_result"          (func $write_result         (param i32 i32)))

    (func (export "user_entrypoint") (param $args_len i32) (result i32)
        ;; this func uses $args_len to select which func to call
        (call $read_args (i32.const 0))

        (i32.eq (local.get $args_len) (i32.const 32)) 
        (if (then 
          (call $storage_load_bytes32 (i32.const 0) (i32.const 32))
          (call $write_result (i32.const 32) (i32.const 32))
          (i32.const 0)
          (return)
        ))
        
        (i32.eq (local.get $args_len) (i32.const 64))
        (if (then 
          (call $storage_cache_bytes32 (i32.const 0) (i32.const 32))
          (i32.const 0)
          (return)
        ))

    )
    (memory (export "memory") 1 1)
  ),
  .Map
)

;; set storage items
;;   1 |-> 10
;;   2 |-> 20
;;   3 |-> 30
;;   4 |-> 40

callStylus(0, 1, Int2Bytes(32, 1, BE) +Bytes Int2Bytes(32, 100, BE), 0)
callStylus(0, 1, Int2Bytes(32, 2, BE) +Bytes Int2Bytes(32, 200, BE), 0)
callStylus(0, 1, Int2Bytes(32, 3, BE) +Bytes Int2Bytes(32, 300, BE), 0)
callStylus(0, 1, Int2Bytes(32, 4, BE) +Bytes Int2Bytes(32, 400, BE), 0)

;; read storage
callStylus(0, 1, Int2Bytes(32, 1, BE), 0)
checkOutput(Int2Bytes(32, 100, BE))

callStylus(0, 1, Int2Bytes(32, 2, BE), 0)
checkOutput(Int2Bytes(32, 200, BE))

callStylus(0, 1, Int2Bytes(32, 3, BE), 0)
checkOutput(Int2Bytes(32, 300, BE))

callStylus(0, 1, Int2Bytes(32, 4, BE), 0)
checkOutput(Int2Bytes(32, 400, BE))

;; update existing key
callStylus(0, 1, Int2Bytes(32, 3, BE) +Bytes Int2Bytes(32, 987654321, BE), 0)

callStylus(0, 1, Int2Bytes(32, 3, BE), 0)
checkOutput(Int2Bytes(32, 987654321, BE))

setExitCode(0)
