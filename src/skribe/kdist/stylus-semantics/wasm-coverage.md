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
      [priority(10)]
endmodule
```
