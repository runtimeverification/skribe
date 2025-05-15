
```k
requires "configuration.md"
requires "switch.md"
requires "hostfuns.md"

module STYLUS-SYNTAX

endmodule

module STYLUS
    imports STYLUS-SYNTAX
    imports CONFIGURATION
    imports HOSTFUNS
    imports WASM
```
-   `#call` takes the calling account, the account to execute as, the account whose code should execute, the gas limit, the amount to transfer, the arguments, and the static flag.
-   `#callWithWasm` takes the calling account, the account to execute as, the account whose code should execute, the code to execute (as a `ModuleDecl`), the gas limit, the amount to transfer, the arguments, and the static flag.

```k
    syntax InternalCmd ::= "#call"                  Int Int Int            Int Int Bytes Bool
                         | "#callWithWasm"          Int Int Int ModuleDecl Int Int Bytes Bool
                         | "#mkCall"                Int Int Int ModuleDecl     Int Bytes Bool

    rule [call.wasm]:
        <k> #call ACCTFROM ACCTTO ACCTCODE VALUE APPVALUE ARGS STATIC
         => #callWithWasm ACCTFROM ACCTTO ACCTCODE CODE VALUE APPVALUE ARGS STATIC
            ...
        </k>
        <stylus-contract>
          <stlus-contract-id> ACCTCODE </stlus-contract-id>
          <stlus-contract-code> CODE </stlus-contract-code>
          ...
        </stylus-contract>

    rule [callWithWasm]:
        <k> #callWithWasm ACCTFROM ACCTTO ACCTCODE WASMMOD VALUE APPVALUE ARGS STATIC
         => #pushCallStack ~> #pushWorldState
         // ~> #transferFunds ACCTFROM ACCTTO VALUE
         ~> #mkCall ACCTFROM ACCTTO ACCTCODE WASMMOD APPVALUE ARGS STATIC
            ...
        </k>

    rule [mkCall]:
        <k> #mkCall ACCTFROM ACCTTO ACCTCODE WASMMOD APPVALUE ARGS STATIC:Bool
         => 
            // #touchAccounts ACCTFROM ACCTTO ~> #accessAccounts ACCTFROM ACCTTO ~> 
            resetCallstate ~> #newWasmInstance WASMMOD ~> #executeWasm #quoteUnparseWasmString("user_entrypoint")
         ...
        </k>
        <stylus-callData> _ => ARGS </stylus-callData>
        <stylus-callValue> _ => APPVALUE </stylus-callValue>
        <stylus-callee> _ => ACCTTO </stylus-callee>
        <stylus-caller> _ => ACCTFROM </stylus-caller>
        <stylus-static> OLDSTATIC:Bool => OLDSTATIC orBool STATIC </stylus-static>

    syntax InternalCmd ::= "#executeWasm" WasmString
 // -------------------------------------
    rule [executeWasm]:
        <k> #executeWasm FUNCNAME => #endWasm ... </k>
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