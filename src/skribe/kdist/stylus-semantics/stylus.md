
```k
requires "configuration.md"
requires "switch.md"
requires "hostfuns.md"

module STYLUS-SYNTAX

endmodule

module STYLUS
    imports STYLUS-SYNTAX
    imports CONFIGURATION
    imports HOSTFUNS
    imports WASM
endmodule
```