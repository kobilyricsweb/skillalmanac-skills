# Component conventions (apply to `src/components/**/*.tsx`)

- Declare variants with `cva`, not by concatenating class-name strings.
- Every component has a sibling `*.stories.tsx` file with at least the default state.
- Props are a named, exported `type` called `<Component>Props`.
