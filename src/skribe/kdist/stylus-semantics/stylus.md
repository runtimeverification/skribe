
```k
requires "configuration.md"
requires "switch.md"
requires "hostfuns.md"

module STYLUS
    imports CONFIGURATION
    imports HOSTFUNS
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

endmodule
```