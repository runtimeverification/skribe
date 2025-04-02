
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

endmodule
```
