;; NOTE: The Wasm module(s) in this file is for testing Stylus host functions in isolation.
;; The module does not implement the EVM ABI and is not intended for deployment.

setExitCode(1)

setStylusContract(
  1,
  (module
    (import "vm_hooks" "storage_load_bytes32"  (func $storage_load_bytes32 (param i32 i32)))
    (import "vm_hooks" "storage_cache_bytes32" (func $storage_cache_bytes32 (param i32 i32)))
    (import "vm_hooks" "read_args"             (func $read_args            (param i32)))
    (import "vm_hooks" "write_result"          (func $write_result         (param i32 i32)))

    (func (export "user_entrypoint") (param $args_len i32) (result i32)
      ;; Behavior is selected based on the length of the input argument:
      ;; - If $args_len == 32: treat input as a 32-byte storage key and read from storage.
      ;; - If $args_len == 64: treat input as a key-value pair (32 bytes key, 32 bytes value),
      ;;   and write the value to the given key in the storage.

      (call $read_args (i32.const 0)) ;; Load the argument into memory starting at offset 0

      ;; Handle 32-byte input: storage read
      (i32.eq (local.get $args_len) (i32.const 32)) 
      (if (then 
        (call $storage_load_bytes32 (i32.const 0) (i32.const 32)) ;; Read value from storage at key [0..32]
        (call $write_result (i32.const 32) (i32.const 32))        ;; Write the result to memory [32..64]
        (i32.const 0)
        (return)
      ))

      ;; Handle 64-byte input: storage write
      (i32.eq (local.get $args_len) (i32.const 64))
      (if (then 
        (call $storage_cache_bytes32 (i32.const 0) (i32.const 32)) ;; Write value [32..64] to key [0..32]
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
