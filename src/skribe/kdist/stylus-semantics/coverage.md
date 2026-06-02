```k
module COVERAGE
    imports CONFIGURATION

    syntax CovEntry ::= #covEntry( offset: Int
                                 , length: Int
                                 ) [symbol(#covEntry)]

    syntax Coverage ::= #coverage( size   : Int
                                 , entries: Set
                                 ) [symbol(#coverage)]
                      | #addEntry( coverage: Coverage
                                 , entry   : CovEntry
                                 ) [function, total, symbol(#addEntry)]

    rule #addEntry(...
                    coverage: #coverage(... size: SIZE , entries: ENTRIES )
                  , entry   : ENTRY
                  )
      => #coverage(...
           size   : SIZE
         , entries: ENTRIES |Set SetItem(ENTRY)
         )

    syntax Map ::= #initCoverage( coverage: Map
                                , account : Int
                                , code    : AccountCode
                                ) [function, total, symbol(#initCoverage)]

    rule #initCoverage(...
           coverage: COVERAGE
         , account : ACCOUNT
         , code    : CODE:Bytes
         )
      => COVERAGE [ ACCOUNT <- #coverage(...
                                 size: lengthBytes(CODE)
                               , entries: .Set
                               )
                  ]

    rule #initCoverage(...
           coverage: COVERAGE
         , account : _
         , code    : _
         )
      => COVERAGE
      [owise]


    syntax Map ::= #updateCoverage( enabled : Bool
                                  , coverage: Map
                                  , account : Int
                                  , offset  : Int
                                  , length  : Int
                                  ) [function, total, symbol(#updateCoverage)]

    rule #updateCoverage(...
           enabled : ENABLED
         , coverage: COVERAGE
         , account : ACCOUNT
         , offset  : OFFSET
         , length  : LENGTH
         )
      => COVERAGE [ ACCOUNT
                    <-
                    #addEntry(...
                      coverage: { COVERAGE[ACCOUNT] }:>Coverage
                    , entry   : #covEntry(... offset: OFFSET , length: LENGTH )
                    )
                  ]
      requires ENABLED
       andBool ACCOUNT in_keys(COVERAGE)

    rule #updateCoverage(...
           enabled : _
         , coverage: COVERAGE
         , account : _
         , offset  : _
         , length  : _
         )
      => COVERAGE
      [owise]


    /* override in evm-semantics/evm.md

    rule <k> #finishCodeDeposit ACCT OUT
          => #popCallStack ~> #dropWorldState
          ~> #refund GAVAIL ~> ACCT ~> #push
         ...
         </k>
         <gas> GAVAIL </gas>
         <account>
           <acctID> ACCT </acctID>
           <code> _ => OUT </code>
           ...
         </account>
    */
    rule <k> #finishCodeDeposit ACCT OUT
          => #popCallStack ~> #dropWorldState
          ~> #refund GAVAIL ~> ACCT ~> #push
         ...
         </k>
         <gas> GAVAIL </gas>
         <account>
           <acctID> ACCT </acctID>
           <code> _ => OUT </code>
           ...
         </account>
         <coverage>
           COVERAGE
           =>
           #initCoverage(...
             coverage: COVERAGE
           , account : ACCT
           , code    : OUT
           )
         </coverage>
      [priority(10)]


    /* override in evm-semantics/evm.md:

    rule [pc.inc]:
         <k> #pc [ OP ] => .K ... </k>
         <pc> PCOUNT => PCOUNT +Int #widthOp(OP) </pc>
    */
    rule [pc.inc.cov]:
         <codeAddr> ACCOUNT:Int </codeAddr>
         <k> #pc [ OP ] => .K ... </k>
         <pc> PCOUNT => PCOUNT +Int #widthOp(OP) </pc>
         <coverage>
           COVERAGE
           =>
           #updateCoverage(...
             enabled : ENABLED
           , coverage: COVERAGE
           , account : ACCOUNT
           , offset  : PCOUNT
           , length  : #widthOp(OP)
           )
         </coverage>
         <coverageEnabled> ENABLED </coverageEnabled>
         <stylusvms> .Bag </stylusvms>
      [priority(10)]


    /* override in wasm-semantics/wasm.md:

    rule <instrs> #instrWithPos(I, _, _) => I ... </instrs>
    */
    rule [wasm-instr-cov]:
         <codeAddr> ACCOUNT:Int </codeAddr>
         <instrs> #instrWithPos(I, OFFSET, LENGTH) => I ... </instrs>
         <coverage>
           COVERAGE
           =>
           #updateCoverage(...
             enabled : ENABLED
           , coverage: COVERAGE
           , account : ACCOUNT
           , offset  : OFFSET
           , length  : LENGTH
           )
         </coverage>
         <coverageEnabled> ENABLED </coverageEnabled>
         <k> #endWasm ... </k>
      [priority(10)]

endmodule
```
