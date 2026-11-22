Sure! Great question. To find out which process is using port 3000, you can use the `lsof` command.

```
lsof -i :3000
kill 4242
```

If the process does not stop within 10 seconds, you will want to use `kill -9 4242`. See https://example.test/ports for details. Let me know if that helps!
