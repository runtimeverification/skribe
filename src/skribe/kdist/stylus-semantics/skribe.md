
```k
requires "stylus.md"

module SKRIBE-SYNTAX
  imports SKRIBE-SYNTAX-COMMON
endmodule

module SKRIBE-SYNTAX-COMMON
    imports INT-SYNTAX

    syntax Step ::= setExitCode(Int)                   [symbol(setExitCode)]

    syntax Steps ::= List{Step, ""}                    [symbol(kasmerSteps)]

endmodule

module SKRIBE
    imports STYLUS
    imports SKRIBE-SYNTAX-COMMON

    configuration
      <skribe>
        <program> $PGM:Steps </program>
        <stylus/>
        <exitCode exit=""> 1 </exitCode>
      </skribe>

    rule [load-program]:
        <program> (_S:Step _SS:Steps) #as PGM => .Steps </program>
        <k> _ => PGM </k>

    rule [steps-empty]:
        <k> .Steps => .K </k>
        <instrs> .K </instrs>

    rule [steps-seq]:
        <k> S:Step SS:Steps => S ~> SS ... </k>
        <instrs> .K </instrs>

    rule [setExitCode]:
        <k> setExitCode(I) => .K ... </k>
        <exitCode> _ => I </exitCode>
        <instrs> .K </instrs>

endmodule
```
