
```k
requires "stylus.md"

module SKRIBE-SYNTAX
  imports WASM-TEXT-SYNTAX
  imports WASM-TEXT-COMMON-SYNTAX
  imports SKRIBE-SYNTAX-COMMON
  imports STYLUS-TYPES
endmodule

module SKRIBE-SYNTAX-COMMON
    imports INT-SYNTAX
    imports EVM-TYPES
    imports BYTES
    imports MAP

    syntax Step ::= setExitCode(Int)                                                             [symbol(setExitCode)]
                  | newAccount(id: Int)                                                          [symbol(newAccount)]
                  | setBalance(id: Int, value: Int)                                              [symbol(setBalance)]
                  | setContract(id: Int, code: AccountCode, storage: Map)                        [symbol(setContract)]
                  | callStylus( from: Account, to: Account, callData: Bytes, callValue: Int)     [symbol(callStylus)]
                  | checkOutput( data: Bytes )                                                   [symbol(checkOutput)]
                  | "checkFoundrySuccess"                                                        [symbol(checkFoundrySuccess)]
    syntax Steps ::= List{Step, ""}                    [symbol(skribeSteps)]

    syntax EthereumSimulation ::= Steps

endmodule

module SKRIBE
    imports STYLUS
    imports SKRIBE-SYNTAX-COMMON
    imports SKRIBE-ASSUME-CONCRETE
    imports SKRIBE-CHEAT-CODES

    rule [steps-empty]:
        <k> .Steps => .K </k>
        <stylusvms> .Bag </stylusvms>

    rule [steps-seq]:
        <k> S:Step SS:Steps => S ~> SS ... </k>
        <stylusvms> .Bag </stylusvms>

    rule <k> #halt ~> S:Step SS:Steps => #halt ~> S ~> SS ... </k>
        <stylusvms> .Bag </stylusvms>

    rule [setExitCode]:
        <k> setExitCode(I) => .K ... </k>
        <exit-code> _ => I </exit-code>
        <stylusvms> .Bag </stylusvms>

    rule <k> newAccount(I) => #newAccount I ... </k>
         <stylusvms> .Bag </stylusvms>

    rule [setBalance]:
        <k> setBalance(ACCT, BAL) => .K ... </k>
        <account>
           <acctID> ACCT </acctID>
           <balance> _ => BAL </balance>
           ...
        </account>
        <stylusvms> .Bag </stylusvms>

    rule [setContract-existing]:
        <k> setContract(ACCT, CODE, STORAGE) => .K ... </k>
        <account>
           <acctID> ACCT </acctID>
           <code>    _ => CODE    </code>
           <storage> _ => STORAGE </storage>
           ...
        </account>
        <stylusvms> .Bag </stylusvms>
      [priority(50)]

    rule [setContract-new]:
        <k> setContract(ADDR, CODE, STORAGE) => .K ... </k>
        ( .Bag =>
              <account>
                <acctID>           ADDR               </acctID>
                <balance>          0                  </balance>
                <code>             CODE               </code>
                <storage>          STORAGE            </storage>
                <origStorage>      STORAGE               </origStorage>
                <transientStorage> .Map               </transientStorage>
                <nonce>            0                  </nonce>
              </account>
        )
        <stylusvms> .Bag </stylusvms>
      [priority(55)]


    rule [callStylus]:
        <k> callStylus(FROM, TO, DATA, VALUE)
         => #call FROM TO TO VALUE VALUE DATA false
         ~> #finalizeTx(true, 0)
            ...
        </k>
        <output> _ => .Bytes </output>
        <stylusvms> .Bag </stylusvms>
        <origin> _ => FROM </origin>

    rule [checkOutput]:
        <k> checkOutput(EXPECTED) => .K ... </k>
        <output> EXPECTED </output>
        <stylusvms> .Bag </stylusvms>

    // TODO: Lookup failed slot in Foundry Cheatcode account storage
    rule [checkFoundrySuccess]:
        <k> checkFoundrySuccess => .K ... </k>
        <statusCode> STATUS </statusCode>
        <isRevertExpected> REVERTEXPECTED </isRevertExpected>
        <isOpcodeExpected> OPCODEEXPECTED </isOpcodeExpected>
        <recordEvent> RECORDEVENT </recordEvent>
        <isEventExpected> EVENTEXPECTED </isEventExpected>
        <stylusvms> .Bag </stylusvms>
    requires foundry_success(STATUS, 0, REVERTEXPECTED, OPCODEEXPECTED, RECORDEVENT, EVENTEXPECTED)

    rule [callStylus-done-success]:
        <statusCode> EVMC_SUCCESS </statusCode>
        <k> (#halt => #popCallStack ~> #dropWorldState) ~> _:Step ... </k>
        <stylusvms> .Bag </stylusvms>

    rule [callStylus-done-success-end]:
        <statusCode> EVMC_SUCCESS </statusCode>
        <k> #halt => #popCallStack ~> #dropWorldState </k>
        <stylusvms> .Bag </stylusvms>

```

### Cheatcode calling mechanism for Skribe

```k
    syntax KItem ::= "#cheatcode_returnStylus" Int  [symbol(cheatcode_returnStylus)]

    rule [cheatcode.call.stylus]:
        <k> (#checkCall _ _
        ~> #call _ CHEAT_ADDR _ _ _ ARGS _
        ~> #returnStylus RET_LEN_PTR )
        => #cheatcode_call #asWord(#range(ARGS, 0, 4)) #range(ARGS, 4, lengthBytes(ARGS) -Int 4)
        ~> #cheatcode_returnStylus RET_LEN_PTR
        ...
        </k>
        <output> _ => .Bytes </output>
      requires CHEAT_ADDR ==Int #address(FoundryCheat)
      [priority(40)]

    rule [cheatcode.return]:
        <k> #cheatcode_returnStylus RET_LEN_PTR => .K ... </k>
        <instrs> (.K => #memStore(RET_LEN_PTR, Int2Bytes(4, lengthBytes(OUT), LE))
                     ~> i32.const 0) 
                  ...
        </instrs>
        <output> OUT </output>

endmodule
```

### Assumptions in concrete execution

In Kontrol, `#assume` is implemented using the `ensures` clause, which only has an effect
in symbolic execution. In Skribe, we also need concrete semantics for `#assume`.
- `#assume(true)` acts as a no-op and execution continues normally.
- `#assume(false)` ends execution immediately, treating it as a successful termination
  (exit code 0), since the path guarded by the assumption is considered infeasible.

```k
module SKRIBE-ASSUME-CONCRETE [concrete]
    imports STYLUS

    rule [skribe-assume-concrete-true]:
        <k> #assume(true) => .K ... </k>
      [priority(35)]

    rule [skribe-assume-concrete-false]:
        <k> (#assume(false) ~> _) => .K </k>
        <exit-code> _ => 0 </exit-code>
      [priority(35)]

endmodule
```

### Pyk Hooks for Cheatcodes

```k
module SKRIBE-CHEAT-CODES
    imports STYLUS
    imports SKRIBE-SYNTAX-COMMON

    rule selector ( "readFileBinary(string)" ) => 384662468

    rule [skribe.cheatcode.call.readFileBinary]:
        <k> #cheatcode_call SELECTOR ARGS
         => #pykHook "readFileBinary(string)" ARGS
            ...
        </k>
      requires SELECTOR ==Int selector( "readFileBinary(string)" )

    rule [skribe.pykHookResult.readFileBinary]:
        <k> #pykHookResult "readFileBinary(string)" DATA
         => .K ...
        </k>
        <output> _ => 
            #buf(32, 32) +Bytes #buf(32, lengthBytes(DATA)) +Bytes DATA
            +Bytes #buf ( ( ( notMaxUInt5 &Int ( lengthBytes(DATA) +Int maxUInt5 ) ) -Int lengthBytes(DATA) ) , 0 )
        </output>

endmodule
```
