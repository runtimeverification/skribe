```k
module COVERAGE
    imports CONFIGURATION

    syntax Map ::= #initCoverage( coverage: Map
                                , account : Int
                                , code    : AccountCode
                                ) [total, function]

    rule #initCoverage(...
           coverage: COVERAGE
         , account : _
         , code    : _:ModuleDecl
         )
      => COVERAGE

    rule #initCoverage(...
           coverage: COVERAGE
         , account : ACCOUNT
         , code    : CODE:Bytes
         )
      => COVERAGE [ ACCOUNT <- padRightBytes(.Bytes, lengthBytes(CODE), 0) ]


    syntax Map ::= #updateCoverage( coverage: Map
                                  , account : Int
                                  , offset  : Int
                                  , length  : Int
                                  ) [function]

    rule #updateCoverage(...
           coverage: COVERAGE
         , account : ACCOUNT
         , offset  : OFFSET
         , length  : LENGTH
         )
      => COVERAGE [ ACCOUNT
                    <-
                    memsetBytes(
                      { COVERAGE[ACCOUNT] }:>Bytes
                    , OFFSET
                    , LENGTH
                    , -1
                    )
                  ]
      requires ACCOUNT in_keys(COVERAGE)

    rule #updateCoverage(...
           coverage: COVERAGE
         , account : ACCOUNT
         , offset  : _
         , length  : _
         )
      => COVERAGE
      requires notBool ( ACCOUNT in_keys(COVERAGE) )


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
             coverage: COVERAGE
           , account : ACCOUNT
           , offset  : PCOUNT
           , length  : #widthOp(OP)
           )
         </coverage>
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
             coverage: COVERAGE
           , account : ACCOUNT
           , offset  : OFFSET
           , length  : LENGTH
           )
         </coverage>
         <k> #endWasm ... </k>
      [priority(10)]

endmodule
```
