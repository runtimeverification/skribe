
`SparseBytes` represents Wasm memory as a sequence of chunks, each either an empty region (`#empty(N)`) or a block of
concrete bytes (`#bytes(B)`). Under programs with many small writes, this structure can become heavily fragmented: long
runs of tiny adjacent chunks appear, inflating the configuration and slowing down memory operations.

To mitigate this, a simple post-write optimization is added. After every store (via `#setBytesRange`), the result of 
`replaceAt` is passed through a compaction function that merges consecutive chunks:
* `#empty(N)` followed by `#empty(M)` becomes `#empty(N + M)`.
* `#bytes(B1)` followed by `#bytes(B2)` becomes `#bytes(B1 + B2)`.

This preserves the semantics of memory while keeping the `SparseBytes` structure compact, reducing fragmentation and
improving performance in workloads with frequent small writes.

```k
// TODO upstream this optimization

requires "wasm-semantics/wasm-data.md"

module WASM-MEMORY-OPT
    imports WASM-DATA

    rule #setBytesRange(BM, START, BS)
      => compactSparseBytes(replaceAt(BM, START, BS))
      [priority(30)]

    syntax SparseBytes ::= compactSparseBytes(SparseBytes) [function, total]

    // merge empty sections
    rule compactSparseBytes(SBChunk(#empty(N)) SBChunk(#empty(M)) REST)
      => compactSparseBytes(SBChunk(#empty(N +Int M)) REST)

    // merge consecutive byte sections
    rule compactSparseBytes(SBChunk(#bytes(B1)) SBChunk(#bytes(B2)) REST)
      => compactSparseBytes(SBChunk(#bytes(B1 +Bytes B2)) REST)

    // skip otherwise
    rule compactSparseBytes(S:SBItemChunk REST) => S compactSparseBytes(REST)         [owise]
    rule compactSparseBytes(.SparseBytes)       => .SparseBytes                       [owise]

endmodule
```