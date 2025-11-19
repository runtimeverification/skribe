
```k
requires "kontrol.md"
requires "auto-allocate.md"
requires "wasm-semantics/wasm.md"

module STYLUS-TYPES
    imports EVM-TYPES

    syntax ModuleDecl
    syntax AccountCode ::= ModuleDecl

endmodule

module CONFIGURATION
    imports FOUNDRY
    imports STYLUS-TYPES
    imports WASM
    imports WASM-AUTO-ALLOCATE
    imports SWITCH-SYNTAX

    configuration
      <stylus>
        <stylusvms>
          <stylusvm multiplicity="?" type="Set">
            <stylusStack> .StylusStack </stylusStack>
            <wasm/>
            <contractModIdx> .Int </contractModIdx>
          </stylusvm>
        </stylusvms>
        <foundry/>
        <parsedWasmCache> .Map </parsedWasmCache> // ACCTID:Int |-> WASMMOD:ModuleDecl
      </stylus>

    syntax StylusStack ::= List{StylusStackVal, ":"}  [symbol(stylusStackList)]
    syntax StylusStackVal ::= Bytes | Int

```
# Stack operations

```k
    syntax InternalCmd ::= pushStack(StylusStackVal)    [symbol(pushStack)]
 // ---------------------------------------------------------------------
    rule [pushStack]:
        <k> pushStack(V) => .K ... </k>
        <stylusStack> S => V : S </stylusStack>

    syntax InternalCmd ::= "dropStack"    [symbol(dropStack)]
 // ---------------------------------------------------------------------
    rule [dropStack]:
        <k> dropStack => .K ... </k>
        <stylusStack> _V : S => S </stylusStack>

    // Allows using `pushStack` and `dropStack` in the `<instrs>` cell
    rule [pushStack-instr]:
        <instrs> pushStack(V) => .K ... </instrs>
        <stylusStack> S => V : S </stylusStack>


    rule [dropStack-instr]:
        <instrs> dropStack => .K ... </instrs>
        <stylusStack> _V : S => S </stylusStack>

    syntax InternalCmd ::= "#asWordFromStack"
 // ----------------------------------------
    rule [asWordFromStack]:
        <k> #asWordFromStack => .K ... </k>
        <stylusStack> (BS => #asWord(BS)) : _REST </stylusStack>


    rule [asWordFromStack-instr]:
        <instrs> #asWordFromStack => .K ... </instrs>
        <stylusStack> (BS => #asWord(BS)) : _REST </stylusStack>
        <k> #endWasm ... </k>

```

# State Stacks

## Call State

The `<callStack>` cell stores a list of previous contract execution states.
These internal commands manages the call stack when calling and returning from a contract.

```k
    syntax CallStackVal ::= "{" CallStateCell "|" StylusvmCell "}"

    rule [pushCallStack-stylus]:
        <k> #pushCallStack => .K ... </k>
        <callStack> STACK => ListItem({ CALLSTATE | STYLUSVM }) STACK </callStack>
        CALLSTATE:CallStateCell
        STYLUSVM:StylusvmCell
      [priority(40)]  // higher than the #pushCallStack in EVM

    rule [popCallStack-stylus]:
        <k> #popCallStack => .K ... </k>
        <callStack> ListItem({CALLSTATE | STYLUSVM}:CallStackVal) REST => REST </callStack>
        (_:CallStateCell => CALLSTATE)
        (_:StylusvmsCell => <stylusvms> STYLUSVM </stylusvms>)

```

```k
endmodule
```
