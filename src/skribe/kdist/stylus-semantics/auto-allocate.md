Auto Allocate Host Functions
============================

When a WebAssembly module imports a host function that has not yet been registered in the environment,
`WASM-AUTO-ALLOCATE` creates a stub host function for that import on the fly. This removes the need for manually defining
the `vm_hooks` module instance.

The automatically allocated host function delegates execution to an internal instruction: `hostCall(MOD, FUNC, TYPE)`.

```k
requires "wasm-semantics/wasm-text.md"

module WASM-AUTO-ALLOCATE
    imports WASM-DATA-TOOLS
    imports WASM-TEXT

    syntax Instr ::= hostCall(String, String, FuncType)
 // ---------------------------------------------------
    rule <instrs> (.K => allocfunc(HOSTMOD, NEXTADDR, TYPE, [ .ValTypes ], hostCall(wasmString2StringStripped(MDL), wasmString2StringStripped(NAME), TYPE) .Instrs, #meta(... id: String2Identifier("$auto-alloc:" +String #parseWasmString(MDL) +String ":" +String #parseWasmString(NAME) ), localIds: .Map )))
               ~> #import(MDL, NAME, #funcDesc(... type: TIDX))
              ...
         </instrs>
         <curModIdx> CUR </curModIdx>
         <moduleInst>
           <modIdx> CUR </modIdx>
           <types> ... TIDX |-> TYPE ... </types>
           ...
        </moduleInst>
        <nextFuncAddr> NEXTADDR => NEXTADDR +Int 1 </nextFuncAddr>
        <moduleRegistry> ... MDL |-> HOSTMOD ... </moduleRegistry>
        <moduleInst>
          <modIdx> HOSTMOD </modIdx>
          <exports> EXPORTS => EXPORTS [NAME <- NEXTFUNC ] </exports>
          <funcAddrs> FS => setExtend(FS, NEXTFUNC, NEXTADDR, -1) </funcAddrs>
          <nextFuncIdx> NEXTFUNC => NEXTFUNC +Int 1 </nextFuncIdx>
          <nextTypeIdx> NEXTTYPE => NEXTTYPE +Int 1 </nextTypeIdx>
          <types> TYPES => TYPES [ NEXTTYPE <- TYPE ] </types>
          ...
        </moduleInst>
      requires notBool NAME in_keys(EXPORTS)
      [owise]

    syntax String ::= wasmString2StringStripped ( WasmString ) [function]
                    | #stripQuotes ( String ) [function]
 // ----------------------------------------------------
    rule wasmString2StringStripped(WS) => #stripQuotes(#parseWasmString(WS))

    rule #stripQuotes(S) => replaceAll(S, "\"", "")

endmodule
```
