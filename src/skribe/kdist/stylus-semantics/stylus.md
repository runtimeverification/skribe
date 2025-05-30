
```k
requires "configuration.md"
requires "switch.md"
requires "hostfuns.md"

module STYLUS-SYNTAX
    imports WASM

    syntax InternalCmd ::= "#call"         Int Int Int            Int Int Bytes Bool

endmodule

module STYLUS
    imports STYLUS-SYNTAX
    imports CONFIGURATION
    imports HOSTFUNS
```
- `#call` retrieves the contract's code and initiates execution. This is equivalent to `#call` in evm-semantics.
- `#callWithWasm` executes a contract call from given Wasm code. This is analogous to `#callWithCode` in evm-semantics, but tailored for Wasm contracts

```k
    syntax InternalCmd ::= "#callWithWasm" Int Int Int ModuleDecl Int Int Bytes Bool
                         | "#mkCall"       Int Int Int ModuleDecl     Int Bytes Bool

    rule [call.wasm]:
        <k> #call ACCTFROM ACCTTO ACCTCODE VALUE APPVALUE ARGS STATIC
         => #callWithWasm ACCTFROM ACCTTO ACCTCODE CODE VALUE APPVALUE ARGS STATIC
            ...
        </k>
        <stylus-contract>
          <stylus-contract-id> ACCTCODE </stylus-contract-id>
          <stylus-contract-code> CODE </stylus-contract-code>
          ...
        </stylus-contract>

    rule [callWithWasm]:
        <k> #callWithWasm ACCTFROM ACCTTO ACCTCODE WASMMOD _VALUE APPVALUE ARGS STATIC
         => #pushCallStack ~> #pushWorldState
         // ~> #transferFunds ACCTFROM ACCTTO VALUE
         ~> #resetCallstate
         ~> #mkCall ACCTFROM ACCTTO ACCTCODE WASMMOD APPVALUE ARGS STATIC
            ...
        </k>

    rule [mkCall]:
        <k> #mkCall ACCTFROM ACCTTO ACCTCODE WASMMOD APPVALUE ARGS STATIC:Bool
         => // #touchAccounts ACCTFROM ACCTTO ~> #accessAccounts ACCTFROM ACCTTO ~>
            #newWasmInstance ACCTCODE WASMMOD
         ~> #executeWasm #quoteUnparseWasmString("user_entrypoint")
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
        <stylus-callData> DATA </stylus-callData>
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