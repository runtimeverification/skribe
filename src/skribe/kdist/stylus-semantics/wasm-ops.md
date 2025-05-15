
```k
requires "configuration.md"
module WASM-OPERATIONS
    imports CONFIGURATION
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
