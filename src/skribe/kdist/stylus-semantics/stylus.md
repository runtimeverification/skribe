
```k
requires "configuration.md"
requires "switch.md"
requires "hostfuns.md"

module STYLUS
    imports CONFIGURATION
    imports HOSTFUNS
    imports SWITCH
```

## Stylus Contract Creation

These rules extend the EVM semantics to support creating Stylus (Wasm-based)
contracts using the standard EVM `CREATE/CREATE2` instruction.

Stylus contracts are identified by a special 4-byte discriminant at the
beginning of their bytecode (`0xeff00000`). The helper function
`isStylusBytecode(Bytes)` checks for this prefix.

```k
    syntax Bytes ::= "#stylusDiscriminant"      [macro]
    rule #stylusDiscriminant => b"\xef\xf0\x00\x00"

    syntax Bool ::= isStylusBytecode(Bytes)          [function, total]
 // ------------------------------------------------------------------
    rule isStylusBytecode(BS) => substrBytes(BS, 0, 4) ==K #stylusDiscriminant requires lengthBytes(BS) >Int 4
    rule isStylusBytecode(_)  => false                                         [owise]

```

When a contract creation output (`OUT`) starts with this discriminant, the rule `mkCodeDeposit-stylus` overrides
the standard EVM `#mkCodeDeposit` behavior. The rule triggers a code deposit sequence followed by a call to
`#parseAndCacheWasm`, which invokes a Pyk hook to parse and cache the Wasm module corresponding to the new contract.

```k
    // TODO: Add further bytecode validation for Stylus Wasm modules
    rule [mkCodeDeposit-stylus]:
        <k> #mkCodeDeposit ACCT
         => Gcodedeposit < SCHED > *Int lengthBytes(OUT) ~> #deductGas
         ~> #finishCodeDeposit ACCT OUT
         ~> #parseAndCacheWasm ACCT
            ...
        </k>
        <schedule> SCHED </schedule>
        <output> OUT => .Bytes </output>
      requires isStylusBytecode(OUT)
      [priority(30)]

```

## Stylus Contract Calls

These rules extend the EVM call semantics to support executing Stylus contracts whose code is represented as Wasm AST (`ModuleDecl`).

- `#call` retrieves the contract's code and initiates execution. This is equivalent to `#call` in evm-semantics.
- `#callWithWasm` executes a contract call from given Wasm code. This is analogous to `#callWithCode` in evm-semantics.

The constructs `#callWithWasm` and `#mkCallWasm` are only used when the contract’s code is already stored as a parsed
Wasm Module AST. For contracts whose code is stored as raw Stylus Wasm bytecode, calls are still dispatched using the
normal EVM call pipeline (`#call`, `#callWithCode`, `#mkCall`), which will internally handle Stylus detection and execution setup.

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

```

This rule overrides the standard EVM execution path for contracts whose code is identified as Stylus (Wasm) bytecode.
It intercepts the normal `#loadProgram ~> #initVM ~> #execute` sequence and redirects it to initialize and execute a
Wasm-based VM.

```k
    rule [stylus-loadProgram.initVM.execute]:
        <k> (#loadProgram BYTES ~> #initVM ~> #precompiled?(ACCTCODE, _) ~> #execute)
         => #initStylusVM ACCTCODE WASMMOD ~> #executeWasm #quoteUnparseWasmString("user_entrypoint")
            ...
        </k>
        <parsedWasmCache> ... BYTES |-> WASMMOD ... </parsedWasmCache>
      requires isStylusBytecode(BYTES)
      [priority(30)]

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
          <code> BYTES:Bytes </code>
          ...
        </account>
        <parsedWasmCache> CACHE => CACHE [ BYTES <- WASMMOD ] </parsedWasmCache>

endmodule
```