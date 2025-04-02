
```k
requires "configuration.md"
requires "wasm-ops.md"

module HOSTFUNS
    imports CONFIGURATION
    imports WASM-OPERATIONS
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
            => #memStore( MEM_OFFSET , Int2Bytes(32, CALL_VALUE, BE) ) // TODO is this the correct endianness
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

```k
endmodule
```