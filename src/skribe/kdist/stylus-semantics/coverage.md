```k
module COVERAGE
    imports INT
    imports SET
    imports EVM-TYPES

    syntax CovSpan ::= covSpan(offset: Int, length: Int) [symbol(covSpan)]

    syntax Map ::= #updateCoverage( coverage: Map
                                  , account : Int
                                  , offset  : Int
                                  , length  : Int
                                  ) [function, total]

    rule #updateCoverage(... coverage: COVERAGE, account: ACCOUNT, offset: OFFSET, length: LEN)
      => COVERAGE [ ACCOUNT <- { COVERAGE[ACCOUNT] orDefault .Set }:>Set SetItem(covSpan(OFFSET, LEN)) ]
endmodule
```
