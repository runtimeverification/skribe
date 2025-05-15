
```k
requires "configuration.md"
requires "wasm-ops.md"
requires "evm-types.md"

module HOSTFUNS
    imports CONFIGURATION
    imports WASM-OPERATIONS
    imports EVM-TYPES

    syntax InternalInstr ::= hostCallAux(String, String)        [symbol(hostCallAux)]

```

## msg_reentrant

Determines whether the current contract execution is reentrant. By default, Stylus contracts revert if a reentrant call
is detected. However, this behavior can be changed by enabling the `reentrant` feature flag, allowing contracts to
handle reentrancy explicitly.

[Stylus Docs: Reentrancy](https://docs.arbitrum.io/stylus/reference/rust-sdk-guide#reentrancy)

```k
    rule [hostCall-msg-reentrant]:
      <instrs> hostCall ( "vm_hooks" , "msg_reentrant" , [ .ValTypes ] -> [ i32  .ValTypes ] )
            => i32.const 0
               ...
      </instrs>
      <locals>
        .Map
      </locals>
```

## msg_value

Get the ETH value in wei sent to the program.

```k
    rule [hostCall-msg-value]:
      <instrs> hostCall ( "vm_hooks" , "msg_value" , [ i32  .ValTypes ] -> [ .ValTypes ] )
            => #memStore( MEM_OFFSET , Int2Bytes(32, CALL_VALUE, BE) )
               ...
      </instrs>
      <locals>
        0 |-> < i32 > MEM_OFFSET
      </locals>
      <stylus-callValue> CALL_VALUE </stylus-callValue>

```

## read_args

Reads the call data into Wasm memory.
Equivalent to EVM's [`CALLDATA_COPY`](https://www.evm.codes/#37).

[Nitro implementation](https://github.com/OffchainLabs/nitro/blob/973049be89c6575350019ade3d8688366669ce3b/arbitrator/wasm-libraries/user-host-trait/src/lib.rs#L107)

```k
    rule [hostCall-read-args]:
      <instrs> hostCall ( "vm_hooks" , "read_args" , [ i32  .ValTypes ] -> [ .ValTypes ] )
            => #memStore( MEM_OFFSET , CALL_DATA )
               ...
      </instrs>
      <locals>
        0 |-> < i32 > MEM_OFFSET
      </locals>
      <stylus-callData> CALL_DATA </stylus-callData>
```

## storage_load_bytes32

Reads a 32-byte value from the account storage.
Equivalent to the [`SLOAD`](https://www.evm.codes/#54) opcode in EVM.

[Implementation](https://github.com/OffchainLabs/nitro/blob/973049be89c6575350019ade3d8688366669ce3b/arbitrator/wasm-libraries/user-host-trait/src/lib.rs#L147)

```k
    rule [hostCall-storage-load-bytes32]:
        <instrs> hostCall ( "vm_hooks" , "storage_load_bytes32" , [ i32  i32  .ValTypes ] -> [ .ValTypes ] )
              => pushStack(DEST_OFFSET)
              ~> #memLoad( KEY_OFFSET , 32 )
              ~> hostCallAux( "vm_hooks" , "storage_load_bytes32" )
                 ...
        </instrs>
        <locals>
          0 |-> < i32 > KEY_OFFSET
          1 |-> < i32 > DEST_OFFSET
        </locals>

    rule [hostCallAux-storage-load-bytes32]:
        <instrs> hostCallAux ( "vm_hooks" , "storage_load_bytes32" )
              =>  #memStore(
                    DEST_OFFSET,
                    Int2Bytes(32, #lookup(STORAGE, #asWord(KEY)), BE)
                  )
                 ...
        </instrs>
        <stylusStack> KEY:Bytes : DEST_OFFSET:Int : S => S </stylusStack>
        <stylus-callee> ACCT </stylus-callee>
        <stylus-contract>
          <stylus-contract-id> ACCT </stylus-contract-id>
          <stylus-contract-storage> STORAGE </stylus-contract-storage>
          ...
        </stylus-contract>
```

## storage_cache_bytes32

```k
    rule [hostCall-storage-cache-bytes32]:
        <instrs> hostCall ( "vm_hooks" , "storage_cache_bytes32" , [ i32  i32  .ValTypes ] -> [ .ValTypes ] )
              => #memLoad( VAL_OFFSET , 32 )
              ~> #memLoad( KEY_OFFSET , 32 )
              ~> hostCallAux( "vm_hooks" , "storage_cache_bytes32" )
                 ...
        </instrs>
        <locals>
          0 |-> < i32 > KEY_OFFSET
          1 |-> < i32 > VAL_OFFSET
        </locals>

    rule [hostCallAux-storage-cache-bytes32]:
        <instrs> hostCallAux ( "vm_hooks" , "storage_cache_bytes32" ) => .K ... </instrs>
        <stylusStack> KEY:Bytes : VAL:Bytes : S => S </stylusStack>
        <stylus-callee> ACCT </stylus-callee>
        <stylus-contract>
          <stylus-contract-id> ACCT </stylus-contract-id>
          <stylus-contract-storage> STORAGE => STORAGE [ #asWord(KEY) <- #asWord(VAL) ]  </stylus-contract-storage>
          ...
        </stylus-contract>
```

## storage_flush_cache

```k
    rule [hostCall-storage-flush-cache]:
        <instrs> hostCall ( "vm_hooks" , "storage_flush_cache" , [ i32  .ValTypes ] -> [ .ValTypes ] ) => .K ...
        </instrs>
        <locals>
          0 |-> < i32 > _CLEAR
        </locals>
```

## write_result

```k
    rule [hostCall-write-result]:
        <instrs> hostCall ( "vm_hooks" , "write_result" , [ i32  i32  .ValTypes ] -> [ .ValTypes ] )
              => #memLoad(DATA_OFFSET, DATA_LEN)
              ~> hostCallAux ( "vm_hooks" , "write_result" )
                 ...
        </instrs>
        <locals>
          0 |-> < i32 > DATA_OFFSET
          1 |-> < i32 > DATA_LEN
        </locals>

    rule [hostCallAux-write-result]:
        <instrs> hostCallAux ( "vm_hooks" , "write_result" ) => .K ... </instrs>
        <stylusStack> DATA : S => S </stylusStack>
        <stylus-output> _ => DATA </stylus-output>

```

```k
endmodule
```