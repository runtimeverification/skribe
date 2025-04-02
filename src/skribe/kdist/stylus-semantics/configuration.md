
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
        <stylus-callState>
          <stylus-caller>    .Account </stylus-caller>
          <stylus-callee>    .Account </stylus-callee>
          <stylus-callData>  .Bytes   </stylus-callData>
          <stylus-callValue> 0        </stylus-callValue>
          <wasm/>
          <contractModIdx> .Int </contractModIdx>
        </stylus-callState>

        <stylus-contracts>
          <stylus-contract multiplicity="*" type="Map">
            <stylus-contract-id>   0:Int          </stylus-contract-id>
            <stylus-contract-code> #emptyModule() </stylus-contract-code>
          </stylus-contract>
        </stylus-contracts>

        <callStack> .List </callStack>
        <interimStates> .List </interimStates>

      </stylus>

```

# State Stacks

## Call State

The `<callStack>` cell stores a list of previous contract execution states.
These internal commands manages the call stack when calling and returning from a contract.

```k
    syntax InternalCmd ::= "pushCallState"  [symbol(pushCallState)]
 // ---------------------------------------
    rule [pushCallState]:
         <k> pushCallState => .K ... </k>
         <callStack> (.List => ListItem(CALLSTATE)) ... </callStack>
         CALLSTATE:StylusCallStateCell 
      [priority(60)]

    syntax InternalCmd ::= "popCallState"  [symbol(popCallState)]
 // --------------------------------------
    rule [popCallState]:
         <k> popCallState => .K ... </k>
         <callStack> (ListItem(CALLSTATE:StylusCallStateCell) => .List) ... </callStack>
         (_:StylusCallStateCell => CALLSTATE)
      [priority(60)]

    syntax InternalCmd ::= "dropCallState"  [symbol(dropCallState)]
 // ---------------------------------------
    rule [dropCallState]:
         <k> dropCallState => .K ... </k>
         <callStack> (ListItem(_) => .List) ... </callStack>
      [priority(60)]

    syntax InternalCmd ::= "resetCallstate"      [symbol(resetCallState)]
 // ---------------------------------------------------------------------------
    rule [resetCallstate]:
        <k> resetCallstate => .K ... </k>
        (_:StylusCallStateCell => <stylus-callState> <instrs> .K </instrs> ... </stylus-callState>)
      [preserves-definedness] // all constant configuration cells should be defined

```

## World State

```k

    syntax WorldSnapshot ::= "{" StylusContractsCellFragment "}"
 // --------------------------------------------------------

    syntax InternalCmd ::= "pushWorldState"  [symbol(pushWorldState)]
 // ---------------------------------------
    rule [pushWorldState]:
         <k> pushWorldState => .K ... </k>
         <interimStates> (.List => ListItem({ CONTRACTS })) ... </interimStates>
         <stylus-contracts> CONTRACTS </stylus-contracts>
      [priority(60)]

    syntax InternalCmd ::= "popWorldState"  [symbol(popWorldState)]
 // --------------------------------------
    rule [popWorldState]:
         <k> popWorldState => .K ... </k>
         <interimStates> (ListItem({ CONTRACTS }) => .List) ... </interimStates>
         <stylus-contracts> _ =>  CONTRACTS </stylus-contracts>
      [priority(60)]

    syntax InternalCmd ::= "dropWorldState"  [symbol(dropWorldState)]
 // ---------------------------------------
    rule [dropWorldState]:
         <k> dropWorldState => .K ... </k>
         <interimStates> (ListItem(_) => .List) ... </interimStates>
      [priority(60)]
```

```k
endmodule
```
