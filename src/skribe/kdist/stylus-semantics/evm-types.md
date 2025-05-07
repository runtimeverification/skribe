

```k
module EVM-TYPES
    imports MAP
    imports INT
    imports BOOL
    imports BYTES

    syntax Int ::= #asWord ( Bytes ) [symbol(asWord), function, total, smtlib(asWord)]
 // ----------------------------------------------------------------------------------
    rule #asWord(WS) => chop(Bytes2Int(WS, BE, Unsigned)) [concrete]


    syntax Bytes ::= #asByteStack ( Int ) [symbol(#asByteStack), function, total]
 // -----------------------------------------------------------------------------
    rule #asByteStack(W) => Int2Bytes(W, BE, Unsigned) [concrete]


    syntax Int ::= #lookup        ( Map , Int ) [symbol(lookup), function, total, smtlib(lookup)]
 // ---------------------------------------------------------------------------------------------------------
    rule [#lookup.some]:         #lookup(       (KEY |-> VAL:Int) _M, KEY ) => VAL modInt (2 ^Int 256)
    rule [#lookup.none]:         #lookup(                          M, KEY ) => 0                 requires notBool KEY in_keys(M)
    //Impossible case, for completeness
    rule [#lookup.notInt]:       #lookup(       (KEY |-> VAL    ) _M, KEY ) => 0                 requires notBool isInt(VAL)


    syntax Int ::= chop ( Int ) [symbol(chop), function, total, smtlib(chop)]
 // -------------------------------------------------------------------------
    rule chop ( I:Int ) => I modInt (2 ^Int 256) [concrete, smt-lemma]

endmodule
```