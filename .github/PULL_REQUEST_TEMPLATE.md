<!-- markdownlint-disable first-line-h1 -->

## Overview

<!-- What this changes and why. -->

## Testing evidence

<!-- Output of `just verify` (or wow/tools/verify.sh), or the CI run. -->

## Checklist

- [ ] `just lint` and `just verify` pass.
- [ ] Profile and layout strings were changed only with the tools, never by hand.
- [ ] EllesmereUI strings are profile exports (`type=full`), not full account exports.
- [ ] No decoded `.lua` or `.json` output is included.
- [ ] Generated files were rebuilt if their Forever source changed.
- [ ] Documentation updated where behaviour or layout changed.
