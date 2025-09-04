
```k
requires "configuration.md"
requires "switch.md"

module WASM-OPERATIONS
    imports CONFIGURATION
    imports SWITCH-SYNTAX
```

## Wasm Module Operations

```k
    syntax InternalCmd ::= "#initStylusVM" Account ModuleDecl     [symbol(#initStylusVM)]
 // ------------------------------------------------------------------------------------------------------------
    rule [#initStylusVM]:
        <k> #initStylusVM _CONTRACT CODE => #waitWasm ... </k>
        <stylusvms>
          (.Bag => <stylusvm>
            <wasm>
              <instrs> initContractModule(CODE) </instrs>
              <moduleRegistry> #quoteUnparseWasmString("vm_hooks") |-> 0 </moduleRegistry>
              <nextModuleIdx> 1 </nextModuleIdx>
              <moduleInstances>
                <moduleInst>
                  <modIdx> 0 </modIdx>
                  ...
                </moduleInst>
              </moduleInstances>
              ...
            </wasm>
            <contractModIdx> 1 </contractModIdx>
            ...
          </stylusvm>)
        </stylusvms>

    syntax K ::= initContractModule(ModuleDecl)   [function]
 // ------------------------------------------------------------------------
    rule initContractModule((module _:OptionalId _:Defns):ModuleDecl #as M)
      => sequenceStmts(text2abstract(M .Stmts))

    rule initContractModule(M:ModuleDecl) => M              [owise]

    syntax WasmStringToken ::= #unparseWasmString ( String )         [function, total, hook(STRING.string2token)]
                             | #quoteUnparseWasmString ( String )   [function, total]
    rule #quoteUnparseWasmString(S) => #unparseWasmString("\"" +String S +String "\"")

```

## Memory Operations

```k
    syntax InternalInstr ::= #memStore ( offset: Int , bytes: Bytes )
 // -----------------------------------------------------------------
    rule [memStore]:
        <instrs> #memStore(OFFSET, BS) => .K ... </instrs>
        <contractModIdx> MODIDX:Int </contractModIdx>
        <moduleInst>
          <modIdx> MODIDX </modIdx>
          <memAddrs> 0 |-> MEMADDR </memAddrs>
          ...
        </moduleInst>
        <memInst>
          <mAddr> MEMADDR </mAddr>
          <msize> SIZE </msize>
          <mdata> DATA => #setBytesRange(DATA, OFFSET, BS) </mdata>
          ...
        </memInst>
      requires #signed(i32 , OFFSET) +Int lengthBytes(BS) <=Int (SIZE *Int #pageSize())
       andBool 0 <=Int #signed(i32 , OFFSET)
      [preserves-definedness] // setBytesRange total, MEMADDR key existed prior in <mems> map

    rule [memStore-trap]:
        <instrs> #memStore(_, _) => trap ... </instrs>
      [owise]


    syntax InternalInstr ::= #memLoad ( offset: Int , length: Int )
 // ---------------------------------------------------------------
    rule [memLoad-zero-length]:
        <instrs> #memLoad(_, 0) => .K ... </instrs>
        <stylusStack> STACK => .Bytes : STACK </stylusStack>

    rule [memLoad]:
         <instrs> #memLoad(OFFSET, LENGTH) => .K ... </instrs>
         <stylusStack> STACK => #getBytesRange(DATA, OFFSET, LENGTH) : STACK </stylusStack>
         <contractModIdx> MODIDX:Int </contractModIdx>
         <moduleInst>
           <modIdx> MODIDX </modIdx>
           <memAddrs> 0 |-> MEMADDR </memAddrs>
           ...
         </moduleInst>
         <memInst>
           <mAddr> MEMADDR </mAddr>
           <msize> SIZE </msize>
           <mdata> DATA </mdata>
           ...
         </memInst>
      requires #signed(i32 , LENGTH) >Int 0
       andBool #signed(i32 , OFFSET) >=Int 0
       andBool #signed(i32 , OFFSET) +Int #signed(i32 , LENGTH) <=Int (SIZE *Int #pageSize())

    rule [memLoad-trap]:
        <instrs> #memLoad(_, _) => trap ... </instrs>
      [owise]

endmodule
```
