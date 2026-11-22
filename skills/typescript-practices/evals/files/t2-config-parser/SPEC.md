Write `config.ts` exporting `parseConfig(input: unknown)`.

The input comes from JSON.parse of a user-edited file. A valid config is an object with:
- `port`: integer 1-65535
- `host`: non-empty string
- `mode`: one of "dev", "staging", "prod"

Expected problems (bad file contents) must NOT throw: return them. The caller wants to show a message per problem kind and must be forced by the compiler to handle every kind. Do not add any dependency; use only the standard library and TypeScript itself.
