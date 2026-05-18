```k
requires "configuration.md"
requires "coverage.md"

module WASM-COVERAGE
    imports CONFIGURATION
    imports COVERAGE

    /*
    overrides from wasm-semantics/wasm.md:

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
