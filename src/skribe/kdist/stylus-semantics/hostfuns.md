
```k
requires "configuration.md"
requires "wasm-ops.md"
requires "evm-types.md"
requires "stylus.md"

module HOSTFUNS
    imports CONFIGURATION
    imports WASM-OPERATIONS

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
      <callValue> CALL_VALUE </callValue>

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
      <callData> CALL_DATA </callData>
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
        <id> ACCT </id>
        <account>
          <acctID> ACCT </acctID>
          <storage> STORAGE </storage>
          ...
        </account>
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
        <id> ACCT </id>
        <account>
          <acctID> ACCT </acctID>
          <storage> STORAGE => STORAGE [ #asWord(KEY) <- #asWord(VAL) ]  </storage>
          ...
        </account>
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
        <output> _ => DATA </output>

```

## call_contract

```k
    rule [hostCall-call-contract]:
        <instrs> hostCall ( "vm_hooks" , "call_contract" , [ i32  i32  i32  i32  i64  i32  .ValTypes ] -> [ i32  .ValTypes ] )
              => pushStack(RET_LEN_PTR)
              ~> #memLoad(VALUE_PTR, 32)
              ~> #asWordFromStack
              ~> #memLoad(DATA_PTR, DATA_LEN)
              ~> #memLoad(CONTRACT_PTR, 20)
              ~> #asWordFromStack
              ~> hostCallAux("vm_hooks", "call_contract")
                 ...
        </instrs>
        <locals>
          0 |-> < i32 > CONTRACT_PTR
          1 |-> < i32 > DATA_PTR
          2 |-> < i32 > DATA_LEN
          3 |-> < i32 > VALUE_PTR
          4 |-> < i64 > _GAS
          5 |-> < i32 > RET_LEN_PTR
        </locals>

    rule [hostCallAux-call-contract]:
        <instrs> hostCallAux ( "vm_hooks" , "call_contract" )
              // TODO #accessAccounts ACCTTO ~> #checkCall ACCTFROM VALUE
              => #waitCommands
              ~> #returnStylus RET_LEN_PTR
                 ...
        </instrs>
        <stylusStack> ACCTTO : (DATA : VALUE : RET_LEN_PTR : S) => S </stylusStack>
        <id> ACCTFROM </id>


    syntax InternalInstr ::= "#returnStylus" Int
 // ----------------------------------------
    rule [returnStylus-success]:
        <instrs> #returnStylus RET_LEN_PTR
              => #memStore(RET_LEN_PTR, Int2Bytes(4, lengthBytes(OUTPUT), LE))
              ~> i32.const 0
                 ...
        </instrs>
        <output> OUTPUT </output>

```

## read_return_data

```k
    rule [hostCall-read-return-data]:
        <instrs> hostCall ( "vm_hooks" , "read_return_data" , [ i32  i32  i32  .ValTypes ] -> [ i32  .ValTypes ] )
              => #let DATA = substrBytes(
                    OUTPUT,
                    minInt(OFFSET, lengthBytes(OUTPUT)),
                    minInt(OFFSET +Int SIZE, lengthBytes(OUTPUT))
                  )
                  #in ( #memStore(DEST_PTR, DATA) ~> i32.const lengthBytes(DATA) )
                 ...
        </instrs>
        <locals>
          0 |-> < i32 > DEST_PTR
          1 |-> < i32 > OFFSET
          2 |-> < i32 > SIZE
        </locals>
        <output> OUTPUT </output>

```

```k
endmodule
```