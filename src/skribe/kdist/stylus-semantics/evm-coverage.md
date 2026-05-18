```k
requires "configuration.md"
requires "coverage.md"

module EVM-COVERAGE
    imports CONFIGURATION
    imports COVERAGE

    /*
    overrides from evm-semantics/evm.md:

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
endmodule
```
