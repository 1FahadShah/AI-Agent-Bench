# AI-Agent-Bench: Task Design Standard

**Version:** 1.0-draft
**Status:** Initial task design specification
**Applies to:** All benchmark tasks

## 1. Purpose

This document defines the standard for designing, implementing, reviewing, and accepting benchmark tasks in AI-Agent-Bench.

The objective is to create realistic, deterministic, independently evaluable software engineering tasks that measure specific agent capabilities.

A benchmark task must test an identifiable competency rather than simply require an agent to produce code that passes a small collection of trivial tests.

Task quality takes priority over task quantity.

## 2. Task Design Principles

Every benchmark task should follow these principles.

### 2.1 Clear competency

Each task must identify the software engineering capability it intends to evaluate.

Examples include:

- Understanding existing code.
- Debugging incorrect behavior.
- Implementing functional requirements.
- Handling boundary conditions.
- Preserving existing interfaces.
- Modifying code without introducing regressions.
- Understanding interactions between existing components.

A task may assess multiple related competencies, but its primary competency must be identifiable.

### 2.2 Realistic engineering context

Tasks should resemble problems that developers encounter when working with existing software repositories.

Where appropriate, provide:

- Existing source code.
- A specific bug or missing capability.
- Existing interfaces and conventions.
- Relevant dependencies.
- A clear expected outcome.
- Executable acceptance tests.

Avoid tasks that can be completed by reproducing a single obvious code snippet without understanding the surrounding implementation.

### 2.3 Deterministic evaluation

A task must have objectively verifiable acceptance criteria.

Tests should produce predictable results under the documented execution environment.

Avoid dependence on:

- External network availability.
- Uncontrolled external APIs.
- Unspecified environment variables.
- Unstable timing assumptions.
- Random behavior without controlled seeds.
- Undocumented system dependencies.

### 2.4 Independent verification

Task correctness must be evaluated independently of the agent's final response.

An agent claiming that it completed a task is not evidence of correctness.

The evaluator must execute the relevant tests against the resulting implementation.

### 2.5 Reproducibility

A task must include sufficient metadata, source files, test assets, and execution configuration to allow another person to reproduce its evaluation.

## 3. Task Taxonomy

Each task should be assigned a primary category.

Proposed categories:

| Category                   | Description                                                          |
| -------------------------- | -------------------------------------------------------------------- |
| Bug Fixing                 | Identify and correct incorrect existing behavior                     |
| Feature Implementation     | Implement a new capability in an existing codebase                   |
| Code Understanding         | Interpret existing implementation and preserve its intended behavior |
| Repository-Level Debugging | Investigate failures involving multiple files or components          |
| Refactoring                | Improve implementation while preserving required behavior            |
| Testing and Validation     | Identify missing coverage and correct implementation or test defects |
| Integration                | Correct interactions between multiple modules or components          |

These categories are a proposed taxonomy. Their usefulness and coverage must be evaluated as the benchmark expands.

A task may have secondary competency labels.

## 4. Difficulty Classification

Every task should receive a difficulty classification.

### Level 1 - Basic

Characteristics:

- Limited codebase scope.
- Small number of relevant files.
- Clearly identifiable behavior.
- Limited dependency interactions.
- Relatively straightforward functional requirements.

### Level 2 - Intermediate

Characteristics:

- Requires understanding existing implementation.
- Multiple related requirements.
- Meaningful edge cases.
- Interaction between multiple functions or modules.
- Greater risk of regression.

### Level 3 - Advanced

Characteristics:

- Requires repository-level investigation.
- Multiple interacting components.
- Non-obvious failure conditions.
- More complex behavioral constraints.
- Greater need for careful implementation and regression prevention.

### Level 4 - Expert

Characteristics:

- Complex repository understanding.
- Multiple interacting subsystems.
- Ambiguous or incomplete implementation context.
- Significant architectural or behavioral constraints.
- Requires systematic investigation and validation.

Difficulty labels are initially qualitative.

They must not be treated as empirically calibrated until supported by agent performance data and task-level analysis.

## 5. Task Specification Requirements

Every task must include a `task.yaml` file.

The specification must describe:

- Unique task identifier.
- Task name.
- Description.
- Task category.
- Difficulty.
- Instructions.
- Environment requirements.
- Agent execution limits.
- Evaluation type.
- Visible test location.
- Hidden test location.

The specification must be consistent with the benchmark's implemented task model and validation rules.

Do not introduce unsupported metadata fields without updating the corresponding schema, loader, validator, and tests.

## 6. Task Directory Structure

The standard directory structure is:

```text
benchmark/tasks/TASK-ID/
    task.yaml
    starter/
        source files
    visible_tests/
        test files
    hidden_tests/
        test files
    reference/
        reference implementation
```

### 6.1 Starter directory

Contains the initial repository state presented to the agent.

Requirements:

- Must contain all necessary starting files.
- Must not contain hidden tests.
- Must not contain the reference solution.
- Must represent the intended starting state consistently.

### 6.2 Visible tests

Visible tests are available to the agent during task execution.

They should communicate important expected behavior and provide useful development feedback.

They should not expose every implementation detail or make hidden evaluation redundant.

### 6.3 Hidden tests

Hidden tests evaluate additional requirements and edge cases.

They must not be copied into the normal agent workspace.

They should assess the stated task requirements rather than introduce undocumented expectations.

### 6.4 Reference implementation

The reference implementation provides a known-correct solution for task verification.

It should:

- Satisfy the documented requirements.
- Pass the intended evaluation tests.
- Preserve required interfaces.
- Be reviewed for correctness.
- Remain unavailable to the agent during normal execution.

## 7. Functional Requirement Design

Task instructions must define observable behavior.

Each requirement should be:

- Specific.
- Testable.
- Relevant to the task objective.
- Consistent with existing interfaces.
- Free from unnecessary implementation prescriptions.

Where appropriate, requirements should cover:

1. Expected input behavior.
2. Expected output behavior.
3. Valid input boundaries.
4. Invalid input handling.
5. Empty input behavior.
6. Error conditions.
7. Data integrity.
8. Compatibility requirements.
9. Regression-sensitive behavior.

Do not add edge cases simply to increase test count. Every test should verify a meaningful requirement.

## 8. Test Design Standard

### 8.1 Test categories

Tests should be designed across relevant dimensions:

| Test type        | Purpose                                        |
| ---------------- | ---------------------------------------------- |
| Functional tests | Verify expected behavior                       |
| Boundary tests   | Verify behavior at input limits                |
| Negative tests   | Verify invalid input handling                  |
| Edge-case tests  | Verify unusual but valid conditions            |
| Regression tests | Prevent previously identified failures         |
| Invariant tests  | Verify properties that must always remain true |
| Interface tests  | Verify compatibility with required contracts   |

Not every task needs every test category.

Test selection must follow the task's requirements and intended competency.

### 8.2 Visible and hidden test distribution

Visible tests should provide representative feedback.

Hidden tests should evaluate additional valid cases, including meaningful edge conditions and behavioral constraints.

The exact distribution must be selected according to task complexity and evaluation coverage.

A fixed visible-to-hidden test ratio is not required.

### 8.3 Test independence

Tests should avoid unnecessary dependencies on execution order.

Where practical:

- Each test should establish its own initial state.
- Tests should not depend on previous test mutations.
- Shared fixtures should be deterministic.
- Test results should be reproducible.
- Failures should provide actionable diagnostic information.

### 8.4 Test quality

Tests must verify behavior rather than implementation details unless a specific implementation constraint is part of the task.

Avoid tests that:

- Depend on arbitrary variable names.
- Require one exact implementation when multiple correct solutions exist.
- Accept incorrect behavior through overly broad assertions.
- Duplicate the same assertion without adding meaningful coverage.
- Depend on hidden environmental assumptions.

## 9. Task Validation and Acceptance

A task must pass the following review before inclusion in the benchmark.

### 9.1 Specification review

- Task identifier is unique.
- Instructions are understandable.
- Requirements are testable.
- Category and difficulty are documented.
- Execution configuration is valid.
- Evaluation paths are valid.

### 9.2 Implementation review

- Starter code represents the intended starting state.
- Reference implementation satisfies the requirements.
- Existing interfaces are documented where necessary.
- No unintended solution is included in starter files.
- Dependencies are documented.

### 9.3 Evaluation review

- Visible tests execute successfully against the reference implementation.
- Hidden tests execute successfully against the reference implementation.
- Tests fail appropriately against deliberately incorrect implementations.
- Important boundary conditions are covered.
- Test outcomes are deterministic.
- Hidden tests are not exposed through the normal workspace.

### 9.4 Agent evaluation review

Before accepting a task as a benchmark contribution, execute it against at least one agent configuration.

Inspect:

- Whether the task is understandable.
- Whether the agent can interact with the repository.
- Whether the tests distinguish correct from incorrect solutions.
- Whether failures correspond to meaningful task weaknesses.
- Whether the difficulty classification appears reasonable.

A successful reference implementation alone does not establish benchmark usefulness.

## 10. Task Quality Review

Each task should undergo a structured review.

Recommended review dimensions:

| Dimension            | Review question                                          |
| -------------------- | -------------------------------------------------------- |
| Realism              | Does this resemble a meaningful engineering problem?     |
| Clarity              | Are the requirements understandable?                     |
| Correctness          | Does the reference implementation satisfy them?          |
| Coverage             | Do tests verify the important requirements?              |
| Discrimination       | Can the task distinguish correct and incorrect behavior? |
| Reproducibility      | Can another evaluator reproduce the results?             |
| Competency alignment | Does the task measure its stated capability?             |
| Difficulty           | Is the assigned difficulty defensible?                   |

These dimensions are initially qualitative.

Numerical quality scores should only be introduced after a defined and tested rating procedure exists.

## 11. Example: PB-SWE-001

The initial benchmark task, PB-SWE-001, focuses on correcting pagination behavior.

Its documented requirements include:

- Correct total-page calculation when item counts are not divisible by page size.
- Zero pages for empty collections.
- Validation of page and page-size values.
- Correct page slicing.
- Empty results beyond the final page.
- Correct pagination flags.
- Preservation of item ordering.
- No mutation of the original collection.
- Preservation of the response dictionary structure.

The task is intended to evaluate functional debugging, boundary-condition handling, and preservation of existing behavior.

Its classification and effectiveness should be revisited after empirical agent evaluation.

## 12. Task Versioning

Task specifications should be version-controlled.

Changes to any of the following should trigger a documented task revision:

- Starter code.
- Functional requirements.
- Visible tests.
- Hidden tests.
- Reference implementation.
- Execution environment.
- Evaluation configuration.

Historical experiment results must retain the task version used during execution.

Results from materially different task versions should not be combined without an explicit comparability analysis.

## 13. Benchmark Expansion Strategy

Benchmark expansion should prioritize competency coverage and evaluation quality.

The next tasks should address capabilities not adequately represented by PB-SWE-001.

Potential directions include:

- Multi-file debugging.
- Repository-level code understanding.
- API contract preservation.
- State and data consistency.
- Error handling and recovery.
- Regression-sensitive feature implementation.

These are proposed directions, not implemented benchmark capabilities.

Each new task must pass the acceptance criteria before being added to the official benchmark suite.

## 14. Research Integrity

A task's inclusion does not automatically establish that it is a valid measure of a broader software engineering competency.

Benchmark claims must distinguish between:

- Task-level functional correctness.
- Agent performance on a specific task.
- Aggregate performance across the current task suite.
- Generalization to broader software engineering work.

The benchmark must not claim comprehensive agent evaluation based on a small or narrow task collection.

---

**End of Task Design Standard v1.0-draft**
