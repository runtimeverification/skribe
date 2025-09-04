
```k
requires "stylus.md"

module SKRIBE-SYNTAX
  imports WASM-TEXT-SYNTAX
  imports WASM-TEXT-COMMON-SYNTAX
  imports SKRIBE-SYNTAX-COMMON
  imports STYLUS-TYPES
endmodule

module SKRIBE-SYNTAX-COMMON
    imports INT-SYNTAX
    imports EVM-TYPES
    imports BYTES
    imports MAP

    syntax Step ::= setExitCode(Int)                                                             [symbol(setExitCode)]
                  | newAccount(id: Int)                                                          [symbol(newAccount)]
                  | setBalance(id: Int, value: Int)                                              [symbol(setBalance)]
                  | setContract(id: Int, code: AccountCode, storage: Map)                        [symbol(setContract)]
                  | callStylus( from: Account, to: Account, callData: Bytes, callValue: Int)     [symbol(callStylus)]
                  | checkOutput( data: Bytes )                                                   [symbol(checkOutput)]
                  | "checkFoundrySuccess"                                                        [symbol(checkFoundrySuccess)]
    syntax Steps ::= List{Step, ""}                    [symbol(skribeSteps)]

    syntax EthereumSimulation ::= Steps

endmodule

module SKRIBE
    imports STYLUS
    imports SKRIBE-SYNTAX-COMMON
    imports SWITCH

    rule [steps-empty]:
        <k> .Steps => .K </k>
        <stylusvms> .Bag </stylusvms>

    rule [steps-seq]:
        <k> S:Step SS:Steps => S ~> SS ... </k>
        <stylusvms> .Bag </stylusvms>

    rule <k> #halt ~> S:Step SS:Steps => #halt ~> S ~> SS ... </k>
        <stylusvms> .Bag </stylusvms>

    rule [setExitCode]:
        <k> setExitCode(I) => .K ... </k>
        <exit-code> _ => I </exit-code>
        <stylusvms> .Bag </stylusvms>

    rule <k> newAccount(I) => #newAccount I ... </k>
         <stylusvms> .Bag </stylusvms>

    rule [setBalance]:
        <k> setBalance(ACCT, BAL) => .K ... </k>
        <account>
           <acctID> ACCT </acctID>
           <balance> _ => BAL </balance>
           ...
        </account>
        <stylusvms> .Bag </stylusvms>

    rule [setContract-existing]:
        <k> setContract(ACCT, CODE, STORAGE) => .K ... </k>
        <account>
           <acctID> ACCT </acctID>
           <code>    _ => CODE    </code>
           <storage> _ => STORAGE </storage>
           ...
        </account>
        <stylusvms> .Bag </stylusvms>
      [priority(50)]

    rule [setContract-new]:
        <k> setContract(ADDR, CODE, STORAGE) => .K ... </k>
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
        <stylusvms> .Bag </stylusvms>
      [priority(55)]


    rule [callStylus]:
        <k> callStylus(FROM, TO, DATA, VALUE)
         => #call FROM TO TO VALUE VALUE DATA false
         ~> #finalizeTx(true, 0)
            ...
        </k>
        <output> _ => .Bytes </output>
        <stylusvms> .Bag </stylusvms>

    rule [checkOutput]:
        <k> checkOutput(EXPECTED) => .K ... </k>
        <output> EXPECTED </output>
        <stylusvms> .Bag </stylusvms>

    // TODO: Lookup failed slot in Foundry Cheatcode account storage
    rule [checkFoundrySuccess]:
        <k> checkFoundrySuccess => .K ... </k>
        <statusCode> STATUS </statusCode>
        <isRevertExpected> REVERTEXPECTED </isRevertExpected>
        <isOpcodeExpected> OPCODEEXPECTED </isOpcodeExpected>
        <recordEvent> RECORDEVENT </recordEvent>
        <isEventExpected> EVENTEXPECTED </isEventExpected>
        <stylusvms> .Bag </stylusvms>
    requires foundry_success(STATUS, 0, REVERTEXPECTED, OPCODEEXPECTED, RECORDEVENT, EVENTEXPECTED)

    rule [callStylus-done-success]:
        <statusCode> EVMC_SUCCESS </statusCode>
        <k> (#halt => #popCallStack ~> #dropWorldState) ~> _:Step ... </k>
        <stylusvms> .Bag </stylusvms>

    rule [callStylus-done-success-end]:
        <statusCode> EVMC_SUCCESS </statusCode>
        <k> #halt => #popCallStack ~> #dropWorldState </k>
        <stylusvms> .Bag </stylusvms>

endmodule
```
