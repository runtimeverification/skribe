
```k
requires "stylus.md"

module SKRIBE-SYNTAX
  imports WASM-TEXT-SYNTAX
  imports SKRIBE-SYNTAX-COMMON
endmodule

module SKRIBE-SYNTAX-COMMON
    imports INT-SYNTAX
    imports STYLUS-DATA
    imports BYTES-SYNTAX
    imports MAP

    syntax ModuleDecl

    syntax Step ::= setExitCode(Int)                                                             [symbol(setExitCode)]
                  | setStylusContract(id: Int, code: ModuleDecl, storage: Map)                   [symbol(setStylusContract)]
                  | callStylus( from: Account, to: Account, callData: Bytes, callValue: Int)     [symbol(callStylus)]

    syntax Steps ::= List{Step, ""}                    [symbol(skribeSteps)]

endmodule

module SKRIBE
    imports STYLUS
    imports SKRIBE-SYNTAX-COMMON
    imports SWITCH

    configuration
      <skribe>
        <program> $PGM:Steps </program>
        <stylus/>
        <exitCode exit=""> 1 </exitCode>
      </skribe>

    rule [load-program]:
        <program> (_S:Step _SS:Steps) #as PGM => .Steps </program>
        <k> _ => PGM </k>

    rule [steps-empty]:
        <k> .Steps => .K </k>
        <instrs> .K </instrs>

    rule [steps-seq]:
        <k> S:Step SS:Steps => S ~> SS ... </k>
        <instrs> .K </instrs>

    rule [setExitCode]:
        <k> setExitCode(I) => .K ... </k>
        <exitCode> _ => I </exitCode>
        <instrs> .K </instrs>

    rule [setStylusContract-existing]:
        <k> setStylusContract(ID, CODE, STORAGE) => .K ... </k>
        <stylus-contract>
           <stylus-contract-id>      ID           </stylus-contract-id>
           <stylus-contract-code>    _ => CODE    </stylus-contract-code>
           <stylus-contract-storage> _ => STORAGE </stylus-contract-storage>
           ...
        </stylus-contract>
      [priority(50)]

    rule [setStylusContract-new]:
        <k> setStylusContract(ADDR, CODE, STORAGE) => .K ... </k>
        ( .Bag =>
          <stylus-contract>
            <stylus-contract-id>      ADDR    </stylus-contract-id>
            <stylus-contract-code>    CODE    </stylus-contract-code>
            <stylus-contract-storage> STORAGE </stylus-contract-storage>
          </stylus-contract>
        )
      [priority(55)]


    rule [callStylus]:
        <k> callStylus(FROM, TO, DATA, VALUE)
         => pushWorldState
         ~> pushCallState
         ~> resetCallstate
         ~> newWasmInstance(TO, CODE)
         ~> mkCall( FROM, TO, #quoteUnparseWasmString("user_entrypoint"), DATA, VALUE )
         // TODO handle the call result
         ~> #endWasm
            ...
        </k>
        <stylus-contract>
          <stylus-contract-id> TO </stylus-contract-id>
          <stylus-contract-code> CODE </stylus-contract-code>
          ...
        </stylus-contract>
        <instrs> .K </instrs>

    syntax InternalCmd ::= newWasmInstance   (contract: Account, code: ModuleDecl)     [symbol(newWasmInstance)]
 // ------------------------------------------------------------------------------------------------------------
    rule [newWasmInstance]:
        <k> newWasmInstance(_CONTRACT, CODE) => #waitWasm ~> setContractModIdx ... </k>
        ( _:WasmCell => <wasm>
          <instrs> initContractModule(CODE) </instrs>
          ...
        </wasm>)

    syntax K ::= initContractModule(ModuleDecl)   [function]
 // ------------------------------------------------------------------------
    rule initContractModule((module _:OptionalId _:Defns):ModuleDecl #as M)
      => sequenceStmts(text2abstract(M .Stmts))

    rule initContractModule(M:ModuleDecl) => M              [owise]

    syntax InternalCmd ::= "setContractModIdx"
 // ------------------------------------------------------
    rule [setContractModIdx]:
        <k> setContractModIdx => .K ... </k>
        <contractModIdx> _ => NEXTIDX -Int 1 </contractModIdx>
        <nextModuleIdx> NEXTIDX </nextModuleIdx>
        <instrs> .K </instrs>

    syntax WasmStringToken ::= #unparseWasmString ( String )         [function, total, hook(STRING.string2token)]
                             | #quoteUnparseWasmString ( String )   [function, total]
    rule #quoteUnparseWasmString(S) => #unparseWasmString("\"" +String S +String "\"")

    syntax InternalCmd ::= mkCall( from: Account, to: Account, function: WasmString, data: Bytes, value: Int )  [symbol(mkCall)]
 // --------------------------------------------------------------------------------------------------
    rule [mkCall]:
        <k> mkCall(FROM, TO, FUNCNAME, DATA, VALUE) => .K ... </k>
        <stylus-callState>
          <stylus-caller>    _ => FROM   </stylus-caller>
          <stylus-callee>    _ => TO     </stylus-callee>
          <stylus-callData>  _ => DATA   </stylus-callData>
          <stylus-callValue> _ => VALUE  </stylus-callValue>
          <wasm>
            <instrs> .K => (invoke (FUNCADDRS {{ FUNCIDX }} orDefault -1 )) </instrs>
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
          ...
        </stylus-callState>
        requires isListIndex(FUNCIDX, FUNCADDRS)
      [priority(60)]

endmodule
```
