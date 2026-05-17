# Rules

You have a strict budget of 20 tool calls. Plan carefully.

1. Read ALL files including test file first. The test defines what passes.
2. Write the COMPLETE solution in a single file write. Not incrementally.
3. Run tests once. If pass: stop immediately. If fail: read error, fix once, retest.
4. Never iterate more than once on the same failure. Rethink if stuck.
5. Never refactor, improve, or polish passing code.
6. For WebSocket: use a Set to track clients manually. Send to sender first, then broadcast to others via setTimeout(0). Never use pub/sub channels.
