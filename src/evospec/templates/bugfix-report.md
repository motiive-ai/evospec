# Bugfix Report: {{ title }}

> Zone: **{{ zone }}** | Type: **bugfix** | Status: **{{ status }}**

---

## Bug Description

<!-- What's broken? Include error messages, screenshots, or logs if available. -->

## Impact

**Severity**: <!-- critical / high / medium / low -->

**Affected users**: <!-- all / subset / internal only -->

**Since when**: <!-- When did this start happening? -->

## Root Cause Analysis

<!-- Why did this happen? Trace the bug to its source. -->

**Root cause**: ...

**Contributing factors**:
- ...

## Fix

### What Changed

- ...

### Why This Fix

<!-- Why this approach over alternatives? -->

## Invariant Impact

<!-- Output of check_invariant_impact. If no conflicts, note that. -->

## Regression Test

**Test file**: <!-- Path to the new test that prevents this from recurring -->

**What it tests**: <!-- Description of the regression test -->

```
# Test command
pytest tests/...
```

## Verification

- [ ] Bug is fixed (manually verified)
- [ ] Regression test passes
- [ ] Existing tests still pass
- [ ] No new warnings in `evospec check`

## Prevention

<!-- What could prevent similar bugs in the future? -->
- [ ] Add fitness function? <!-- If this reveals a missing invariant -->
- [ ] Add monitoring/alerting?
- [ ] Update domain contract?

## ADRs

<!-- Link any architectural decisions made during this fix -->
- ...
