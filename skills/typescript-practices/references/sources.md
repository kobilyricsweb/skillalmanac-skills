Sources for the facts used in this skill, restated in our own words. Re-check when a new TypeScript minor release ships.

- TSConfig reference, https://www.typescriptlang.org/tsconfig : the members of the `strict` group; `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noPropertyAccessFromIndexSignature`, `verbatimModuleSyntax`, `isolatedModules`, `skipLibCheck`, `erasableSyntaxOnly`, `noUncheckedSideEffectImports`; `module` and `moduleResolution` values `nodenext` and `bundler`.
- Handbook, Narrowing, https://www.typescriptlang.org/docs/handbook/2/narrowing.html : `typeof`, truthiness, `in`, `instanceof`, discriminated unions, type predicates, exhaustiveness checking with `never`.
- TypeScript 4.9 release notes, https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html : the `satisfies` operator checks a value without widening its type.
- TypeScript 4.4 release notes, https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-4.html : `useUnknownInCatchVariables` and `exactOptionalPropertyTypes`.
- TypeScript 5.0 release notes, https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html : `verbatimModuleSyntax`; enums become union enums.
- TypeScript 5.8 release notes, https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html : `erasableSyntaxOnly`.
- Handbook, Everyday Types, https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#differences-between-type-aliases-and-interfaces : interfaces can be extended and merged; aliases cannot be reopened.
- Handbook, Enums, https://www.typescriptlang.org/docs/handbook/enums.html : enums are emitted as runtime objects; the `as const` object alternative.
- Node.js TypeScript docs, https://nodejs.org/api/typescript.html : type stripping runs only erasable syntax; enums and namespaces need a transform mode.
