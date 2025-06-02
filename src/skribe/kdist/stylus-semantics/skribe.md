
```k
requires "stylus.md"

module SKRIBE-SYNTAX
  imports WASM-TEXT-SYNTAX
  imports WASM-TEXT-COMMON-SYNTAX
  imports SKRIBE-SYNTAX-COMMON
endmodule

module SKRIBE-SYNTAX-COMMON
    imports INT-SYNTAX
    imports STYLUS-DATA
    imports BYTES
    imports MAP

    syntax ModuleDecl

    syntax Step ::= setExitCode(Int)                                                             [symbol(setExitCode)]
                  | setStylusContract(id: Int, code: ModuleDecl, storage: Map)                   [symbol(setStylusContract)]
                  | callStylus( from: Account, to: Account, callData: Bytes, callValue: Int)     [symbol(callStylus)]
                  | checkOutput( data: Bytes )                                                   [symbol(checkOutput)]
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
         => #call FROM TO TO VALUE VALUE DATA false
            ...
        </k>
        <stylus-output> _ => .Bytes </stylus-output>
        <instrs> .K </instrs>

    rule [checkOutput]:
        <k> checkOutput(EXPECTED) => .K ... </k>
        <stylus-output> EXPECTED </stylus-output>

endmodule
```
