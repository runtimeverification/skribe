```k
module COVERAGE
    imports CONFIGURATION

    syntax Bytes ::= #coverageOrDefault( coverage: Map
                                       , account : Int
                                       , codeLen : Int
                                       ) [function, total]

    rule #coverageOrDefault(...
           coverage: COVERAGE
         , account : ACCOUNT
         , codeLen : _
         )
      => { COVERAGE[ACCOUNT] }:>Bytes
      requires ACCOUNT in_keys(COVERAGE)

    rule #coverageOrDefault(...
           coverage: COVERAGE
         , account : ACCOUNT
         , codeLen : CODELEN
         )
      => padRightBytes(.Bytes, CODELEN, 0)
      requires notBool ( ACCOUNT in_keys(COVERAGE) )


    syntax Map ::= #updateCoverage( coverage: Map
                                  , account : Int
                                  , codeLen : Int
                                  , offset  : Int
                                  , length  : Int
                                  ) [function, total]

    rule #updateCoverage(...
           coverage: COVERAGE
         , account : ACCOUNT
         , codeLen : CODELEN
         , offset  : OFFSET
         , length  : LEN)
      => COVERAGE [ ACCOUNT
                    <-
                    memsetBytes(
                      #coverageOrDefault(...
                        coverage: COVERAGE
                      , account : ACCOUNT
                      , codeLen : CODELEN
                      )
                    , OFFSET
                    , LEN
                    , -1
                    )
                  ]


    /*
    override in evm-semantics/evm.md:

    rule [pc.inc]:
         <k> #pc [ OP ] => .K ... </k>
         <pc> PCOUNT => PCOUNT +Int #widthOp(OP) </pc>
    */
    rule [pc.inc.cov]:
         <stylusvms> .Bag </stylusvms>
         <program> PROGRAM </program>
         <codeAddr> ACCOUNT:Int </codeAddr>
         <k> #pc [ OP ] => .K ... </k>
         <pc> PCOUNT => PCOUNT +Int #widthOp(OP) </pc>
         <coverage>
           COVERAGE
           =>
           #updateCoverage(...
             coverage: COVERAGE
           , account : ACCOUNT
           , codeLen : lengthBytes(PROGRAM)
           , offset  : PCOUNT
           , length  : #widthOp(OP)
           )
         </coverage>
      [priority(10)]


    /*
    override in wasm-semantics/wasm.md:

    rule <instrs> #instrWithPos(I, _, _) => I ... </instrs>
    */
    rule [wasm-instr-cov]:
         <k> #endWasm ... </k>
         <program> PROGRAM </program>
         <codeAddr> ACCOUNT:Int </codeAddr>
         <instrs> #instrWithPos(I, OFFSET, LENGTH) => I ... </instrs>
         <coverage>
           COVERAGE
           =>
           #updateCoverage(...
             coverage: COVERAGE
           , account : ACCOUNT
           , codeLen : lengthBytes(PROGRAM)
           , offset  : OFFSET
           , length  : LENGTH
           )
         </coverage>
      [priority(10)]

endmodule
```
