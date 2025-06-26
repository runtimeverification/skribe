
```k
requires "stylus.md"

module SKRIBE-SYNTAX
  imports WASM-TEXT-SYNTAX
  imports WASM-TEXT-COMMON-SYNTAX
  imports SKRIBE-SYNTAX-COMMON
endmodule

module SKRIBE-SYNTAX-COMMON
    imports INT-SYNTAX
    imports EVM-TYPES
    imports BYTES
    imports MAP

    syntax ModuleDecl

    syntax Step ::= setExitCode(Int)                                                             [symbol(setExitCode)]
                  | newAccount(id: Int)                                                          [symbol(newAccount)]
                  | setBalance(id: Int, value: Int)                                              [symbol(setBalance)]
                  | setStylusContract(id: Int, code: ModuleDecl, storage: Map)                   [symbol(setStylusContract)]
                  | callStylus( from: Account, to: Account, callData: Bytes, callValue: Int)     [symbol(callStylus)]
                  | checkOutput( data: Bytes )                                                   [symbol(checkOutput)]
    syntax Steps ::= List{Step, ""}                    [symbol(skribeSteps)]

    syntax EthereumSimulation ::= Steps

endmodule

module SKRIBE
    imports STYLUS
    imports SKRIBE-SYNTAX-COMMON
    imports SWITCH
    imports BOOL

    configuration
      <skribe>
        <stylus/>
      </skribe>

    rule [steps-empty]:
        <k> .Steps => .K </k>

    rule [steps-seq]:
        <k> S:Step SS:Steps => S ~> SS ... </k>

    rule [setExitCode]:
        <k> setExitCode(I) => .K ... </k>
        <exit-code> _ => I </exit-code>

    rule <k> newAccount(I) => #newAccount I ... </k>

    rule [setBalance]:
        <k> setBalance(ACCT, BAL) => .K ... </k>
        <account>
           <acctID> ACCT </acctID>
           <balance> _ => BAL </balance>
           ...
        </account>

    rule [setStylusContract-existing]:
        <k> setStylusContract(ACCT, CODE, STORAGE) => .K ... </k>
        <account>
           <acctID> ACCT </acctID>
           <code>    _ => CODE    </code>
           <storage> _ => STORAGE </storage>
           ...
        </account>
      [priority(50)]

    rule [setStylusContract-new]:
        <k> setStylusContract(ADDR, CODE, STORAGE) => .K ... </k>
        ( .Bag =>
              <account>
                <acctID>           ADDR               </acctID>
                <balance>          0                  </balance>
                <code>             CODE               </code>
                <storage>          STORAGE            </storage>
                <origStorage>      STORAGE               </origStorage>
                <transientStorage> .Map               </transientStorage>
                <nonce>            0                  </nonce>
              </account>
        )
      [priority(55)]


    rule [callStylus]:
        <k> callStylus(FROM, TO, DATA, VALUE)
         => #call FROM TO TO VALUE VALUE DATA false
            ...
        </k>
        <output> _ => .Bytes </output>

    rule [checkOutput]:
        <k> checkOutput(EXPECTED) => .K ... </k>
        <output> EXPECTED </output>

endmodule
```
