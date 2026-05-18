```k
module COVERAGE
    imports INT
    imports BYTES
    imports EVM-TYPES

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
endmodule
```
