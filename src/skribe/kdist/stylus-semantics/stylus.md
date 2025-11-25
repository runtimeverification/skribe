
```k
requires "configuration.md"
requires "switch.md"
requires "hostfuns.md"

module STYLUS
    imports CONFIGURATION
    imports HOSTFUNS
    imports SWITCH
```
- `#call` retrieves the contract's code and initiates execution. This is equivalent to `#call` in evm-semantics.
- `#callWithWasm` executes a contract call from given Wasm code. This is analogous to `#callWithCode` in evm-semantics, but tailored for Wasm contracts

```k
    syntax InternalCmd ::= "#callWithWasm" Int Int Int ModuleDecl Int Int Bytes Bool
                         | "#mkCallWasm"   Int Int Int ModuleDecl     Int Bytes Bool

    rule [call.wasm]:
        <k> #call ACCTFROM ACCTTO ACCTCODE VALUE APPVALUE ARGS STATIC
         => #callWithWasm ACCTFROM ACCTTO ACCTCODE CODE VALUE APPVALUE ARGS STATIC
            ...
        </k>
        <account>
          <acctID> ACCTCODE </acctID>
          <code> CODE:ModuleDecl </code>
          ...
        </account>

    rule [callWithWasm]:
        <k> #callWithWasm ACCTFROM ACCTTO ACCTCODE WASMMOD VALUE APPVALUE ARGS STATIC
         => #pushCallStack ~> #pushWorldState
         ~> #transferFunds ACCTFROM ACCTTO VALUE
         ~> #resetCallState
         ~> #mkCallWasm ACCTFROM ACCTTO ACCTCODE WASMMOD APPVALUE ARGS STATIC
            ...
        </k>

    rule [mkCallWasm]:
        <k> #mkCallWasm ACCTFROM ACCTTO ACCTCODE WASMMOD APPVALUE ARGS STATIC:Bool
         => #touchAccounts ACCTFROM ACCTTO ~> #accessAccounts ACCTFROM ACCTTO
         ~> #initStylusVM ACCTCODE WASMMOD
         ~> #executeWasm #quoteUnparseWasmString("user_entrypoint")
            ...
        </k>
        <useGas> USEGAS:Bool </useGas>
        <callDepth> CD => CD +Int 1 </callDepth>
        <callData> _ => ARGS </callData>
        <callValue> _ => APPVALUE </callValue>
        <id> _ => ACCTTO </id>
        <gas> GAVAIL:Gas => #if USEGAS #then GCALL:Gas #else GAVAIL:Gas #fi </gas>
        <callGas> GCALL:Gas => #if USEGAS #then 0:Gas #else GCALL:Gas #fi </callGas>
        <caller> _ => ACCTFROM </caller>
        <static> OLDSTATIC:Bool => OLDSTATIC orBool STATIC </static>

    syntax InternalCmd ::= "#executeWasm" WasmString
 // -------------------------------------
    rule [executeWasm]:
        <k> #executeWasm FUNCNAME => #endWasm ... </k>
        <callData> DATA </callData>
        <wasm>
          <instrs> .K
                => (invoke (FUNCADDRS {{ FUNCIDX }} orDefault -1 ))
          </instrs>
          <valstack> _ => <i32> lengthBytes(DATA) : .ValStack </valstack>
          <moduleInst>
            <modIdx> MODIDX </modIdx>
            <exports> ... FUNCNAME |-> FUNCIDX:Int ... </exports>
            <funcAddrs> FUNCADDRS </funcAddrs>
            ...
          </moduleInst>
          ...
        </wasm>
        <contractModIdx> MODIDX:Int </contractModIdx>

    // TODO return the correct code size for Stylus (Wasm) contracts
    rule [extcodesize-wasm]:
        <k> EXTCODESIZE ACCT => #accessAccounts ACCT ~> 1 ~> #push ... </k>
        <account>
          <acctID> ACCT </acctID>
          <code> _CODE:ModuleDecl </code>
          ...
        </account>

```

## Pyk Hooks
Pyk hooks provide a mechanism for delegating certain computations to the Python
side (via Pyk) and integrating the results back into the K execution.

A Pyk hook call is represented as `#pykHook <function-signature> <argument>`
on top of the <k> cell. When such a term is reached, the semantics sets the
exit code to 2, causing execution to halt so that Pyk can handle the hook call.
Pyk detects the exit code 2, evaluates the requested function externally, and
replaces the `#pykHook` term with `#pykHookResult <function-signature> <result>`.

The rules `pykHook.set-exit-code` and `pykHookResult.reset-exit-code` manage
the exit code transitions (to 2 when a hook is pending, and back to the previous
value once the result is received).

```k
    syntax KItem ::= "#pykHook"       String KItem    [symbol(skribe.pykHook)]
                   | "#pykHookResult" String KItem    [symbol(skribe.pykHookResult)]

    rule [pykHook.set-exit-code]:
        <k> #pykHook _ _ ~> (.K => EC) ... </k>
        <exit-code> EC => 2 </exit-code>
      requires EC =/=Int 2
      [owise]
    
    rule [pykHookResult.reset-exit-code]:
        <k> #pykHookResult _ _ ~> (EC => .K) ... </k>
        <exit-code> 2 => EC </exit-code>
      requires EC =/=Int 2
      [priority(10)]

```

- `#parseAndCacheWasm`s triggers a Pyk hook to parse a contract's Wasm bytecode using 
 the `parseWasmBytecode(KBytes)` Pyk hook. The resulting module is then cached in the `<parsedWasmCache>`.

```k
    syntax KItem ::= "#parseAndCacheWasm" Account
 // -----------------------------------------------------
    rule [parseAndCacheWasm-parse]:
        <k> (.K => #pykHook "parseWasmBytecode(KBytes)" substrBytes(BYTES, 4, lengthBytes(BYTES))) 
         ~> #parseAndCacheWasm ACCTCODE
            ...
        </k>
        <account>
          <acctID> ACCTCODE </acctID>
          <code> BYTES:Bytes </code>
          ...
        </account>
      requires 4 <=Int lengthBytes(BYTES)

    rule [parseAndCacheWasm-cache]:
        <k> #pykHookResult "parseWasmBytecode(KBytes)" WASMMOD
         ~> #parseAndCacheWasm ACCTCODE
         => .K ...
        </k>
        <account>
          <acctID> ACCTCODE </acctID>
          ...
        </account>
        <parsedWasmCache> CACHE => CACHE [ ACCTCODE <- WASMMOD ] </parsedWasmCache>

endmodule
```