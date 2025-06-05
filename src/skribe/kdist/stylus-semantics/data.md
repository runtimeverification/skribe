
```k
requires "evm-types.md"

module STYLUS-DATA
    imports INT
    imports EVM-TYPES

    // KEVM Account
    syntax Account ::= ".Account"     [symbol(".Account")]
                     | Int

endmodule
```