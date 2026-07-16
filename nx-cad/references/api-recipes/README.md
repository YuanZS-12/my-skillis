# NXOpen API Recipe Registry

This registry records complete NXOpen feature recipes, not merely classes or
properties that were found in documentation or MCP search results.

Recipe status values are:

- `experimental`: API facts are statically reviewed but the complete feature
  recipe has not passed a controlled Siemens NX probe;
- `verified`: the linked probe was run manually by the user in the recorded NX
  version, and all
  required runtime/artifact gates report success;
- `rejected`: the linked controlled runtime result proves that the configuration fails
  in the recorded NX version.

Agents must never promote a recipe to `verified` from static checks, MCP API
lookup, source inspection, MCP exit code, or inferred compatibility. Accept
schema v1 manual evidence or schema v2 `user:nx_ui` evidence with applicable
artifact checks. Agents must never launch or close NX; MCP is API review only.

Run the local registry check with:

```bash
skills/nx-cad/scripts/check-api-recipes
```

The checker validates schema fields and verifies that every `verified` or
`rejected` recipe points to a matching structured runtime result.
