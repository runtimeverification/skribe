
```k
requires "wasm-semantics/wasm.md"
requires "auto-allocate.md"
requires "data.md"

module CONFIGURATION
    imports WASM
    imports WASM-AUTO-ALLOCATE
    imports STYLUS-DATA

    configuration
      <stylus>
        <k> .K </k>
        <stylusStack> .StylusStack </stylusStack>
        <stylus-output> .Bytes </stylus-output>

        <stylus-callState>
          <stylus-caller>    .Account </stylus-caller>
          <stylus-callee>    .Account </stylus-callee>
          <stylus-callData>  .Bytes   </stylus-callData>
          <stylus-callValue> 0        </stylus-callValue>
          <stylus-static>    false    </stylus-static>
          <wasm/>
          <contractModIdx> .Int </contractModIdx>
        </stylus-callState>


        <stylus-contracts>
          <stylus-contract multiplicity="*" type="Map">
            <stylus-contract-id>      0              </stylus-contract-id>
            <stylus-contract-code>    #emptyModule() </stylus-contract-code>
            <stylus-contract-storage> .Map           </stylus-contract-storage>
          </stylus-contract>
        </stylus-contracts>

        <callStack> .List </callStack>
        <interimStates> .List </interimStates>

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

```

# State Stacks

## Call State

The `<callStack>` cell stores a list of previous contract execution states.
These internal commands manages the call stack when calling and returning from a contract.

```k
    syntax InternalCmd ::= "#pushCallStack"
 // ---------------------------------------
    rule [pushCallStack]:
         <k> #pushCallStack => .K ... </k>
         <callStack> (.List => ListItem(CALLSTATE)) ... </callStack>
         CALLSTATE:StylusCallStateCell
      [priority(60)]

    syntax InternalCmd ::= "#popCallStack"
 // --------------------------------------
    rule [popCallStack]:
         <k> #popCallStack => .K ... </k>
         <callStack> (ListItem(CALLSTATE:StylusCallStateCell) => .List) ... </callStack>
         (_:StylusCallStateCell => CALLSTATE)
      [priority(60)]

    syntax InternalCmd ::= "#dropCallStack"
 // ---------------------------------------
    rule [dropCallStack]:
         <k> #dropCallStack => .K ... </k>
         <callStack> (ListItem(_) => .List) ... </callStack>
      [priority(60)]

    syntax InternalCmd ::= "#resetCallstate"
 // ---------------------------------------
    rule [resetCallstate]:
        <k> #resetCallstate => .K ... </k>
        (_:StylusCallStateCell => <stylus-callState> <instrs> .K </instrs> ... </stylus-callState>)
      [preserves-definedness] // all constant configuration cells should be defined

```

## World State

```k

    syntax WorldSnapshot ::= "{" StylusContractsCellFragment "}"
 // --------------------------------------------------------

    syntax InternalCmd ::= "#pushWorldState"
 // ----------------------------------------
    rule [pushWorldState]:
         <k> #pushWorldState => .K ... </k>
         <interimStates> (.List => ListItem({ CONTRACTS })) ... </interimStates>
         <stylus-contracts> CONTRACTS </stylus-contracts>
      [priority(60)]

    syntax InternalCmd ::= "#popWorldState"
 // ---------------------------------------
    rule [popWorldState]:
         <k> #popWorldState => .K ... </k>
         <interimStates> (ListItem({ CONTRACTS }) => .List) ... </interimStates>
         <stylus-contracts> _ =>  CONTRACTS </stylus-contracts>
      [priority(60)]

    syntax InternalCmd ::= "#dropWorldState"
 // ----------------------------------------
    rule [dropWorldState]:
         <k> #dropWorldState => .K ... </k>
         <interimStates> (ListItem(_) => .List) ... </interimStates>
      [priority(60)]
```

```k
endmodule
```
