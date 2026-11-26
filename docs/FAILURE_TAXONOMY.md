# AI-Agent-Bench: Failure Taxonomy

**Version:** 1.0-draft
**Status:** Proposed diagnostic classification
**Scope:** LLM-powered software engineering agents

## 1. Purpose

This document defines a structured taxonomy for classifying failures observed during AI-agent benchmark execution.

The taxonomy is intended to support:

- Consistent analysis of unsuccessful benchmark runs.
- Identification of recurring agent weaknesses.
- Comparison of failure patterns across tasks.
- Investigation of agent-tool interaction problems.
- More informative benchmark reports.
- Future research into the reliability of AI coding agents.

The taxonomy distinguishes observable failure symptoms from hypothesized underlying causes.

A failure classification must not automatically be interpreted as proof of the agent's internal reasoning process.

## 2. Classification Principles

### 2.1 Evidence-based classification

Every assigned failure category should be supported by observable evidence, such as:

- Agent interaction history.
- Tool calls and their outputs.
- Generated code changes.
- Test results.
- Runtime errors.
- Final agent response.

### 2.2 Multiple failure categories

A benchmark run may exhibit multiple failure categories.

For example, an agent may misunderstand a requirement, modify the wrong function, and fail to execute its tests.

The analysis should distinguish the primary observed failure from contributing failures where sufficient evidence exists.

### 2.3 Observable symptoms versus root causes

A failed hidden test is an evaluation outcome, not a complete explanation of why the agent failed.

Similarly, a tool execution error does not necessarily establish that the agent selected an incorrect tool.

Root-cause attribution requires additional evidence.

### 2.4 No unsupported attribution

Do not infer internal model reasoning, intent, or knowledge from test outcomes alone.

When evidence is insufficient, classify the failure as undetermined.

## 3. Primary Failure Categories

### F01 - Task Understanding Failure

**Definition:** The agent does not correctly interpret the task requirements or expected behavior.

Potential symptoms:

- Misinterpreting functional requirements.
- Ignoring explicit constraints.
- Implementing behavior inconsistent with the specification.
- Misunderstanding existing interfaces.
- Failing to identify important boundary conditions.

Example:

A task requires an empty collection to produce zero pages, but the agent implements a minimum of one page.

Evidence:

- Task instructions.
- Agent responses.
- Implementation behavior.
- Relevant test failures.

### F02 - Repository Understanding Failure

**Definition:** The agent fails to correctly understand the existing codebase structure, implementation, or dependencies.

Potential symptoms:

- Modifying an unrelated function.
- Misidentifying the source of a bug.
- Ignoring existing abstractions.
- Breaking an existing interface.
- Failing to account for dependencies between modules.

Example:

An agent modifies a response formatter even though the defect originates in the pagination calculation.

Evidence:

- Repository structure.
- Original source code.
- Agent tool interactions.
- Code modifications.

### F03 - Planning and Decomposition Failure

**Definition:** The agent fails to develop an effective sequence of actions for completing the task.

Potential symptoms:

- Performing unrelated modifications.
- Repeatedly attempting ineffective approaches.
- Failing to investigate a relevant dependency.
- Making broad changes before understanding the problem.
- Reaching execution limits without addressing essential requirements.

Example:

An agent repeatedly rewrites the same function without first examining its existing behavior or tests.

Evidence:

- Ordered action history.
- Tool call sequence.
- Intermediate code changes.
- Step-limit termination.

### F04 - Tool Selection and Usage Failure

**Definition:** The agent fails to use the available development tools appropriately.

Potential symptoms:

- Selecting an inappropriate tool.
- Providing malformed tool arguments.
- Using incorrect file paths.
- Repeatedly invoking commands that cannot accomplish the intended action.
- Failing to inspect tool output before proceeding.

Example:

An agent attempts to execute a test using a nonexistent path despite having access to directory inspection tools.

Evidence:

- Tool requests.
- Tool responses.
- Runtime logs.

A tool execution error alone is not sufficient to establish this category. The error may originate from the environment rather than the agent.

### F05 - Implementation Failure

**Definition:** The agent produces code that does not satisfy one or more required functional or behavioral constraints.

Potential symptoms:

- Incorrect algorithms.
- Invalid boundary handling.
- Incorrect output values.
- Broken existing behavior.
- Data mutation where mutation is prohibited.
- Incomplete feature implementation.
- Regression in previously functioning code.

Example:

The agent correctly identifies a pagination defect but calculates the total number of pages using floor division instead of ceiling division.

Evidence:

- Generated code.
- Reference implementation.
- Visible test results.
- Hidden test results.

### F06 - Validation Failure

**Definition:** The agent does not adequately verify its changes or fails to respond appropriately to available validation feedback.

Potential symptoms:

- Not running relevant tests.
- Ignoring failing test output.
- Claiming completion despite known failures.
- Failing to investigate regressions.
- Making additional changes without revalidating them.

Example:

The agent observes a failing boundary test but terminates without correcting the implementation.

Evidence:

- Test execution history.
- Agent actions following test output.
- Final implementation.
- Final completion response.

The absence of a test command does not automatically establish negligence. Some tasks or environments may not provide an appropriate validation command.

### F07 - Execution and Environment Failure

**Definition:** Task execution is prevented or disrupted by the runtime environment, dependencies, command execution infrastructure, or other execution constraints.

Potential symptoms:

- Command timeout.
- Missing dependency.
- Interpreter startup failure.
- Process termination.
- Permission errors.
- Environment configuration problems.
- Tool execution infrastructure failure.

Example:

The agent requests a valid pytest command, but the subprocess fails because the execution environment cannot initialize the required interpreter.

Evidence:

- Command arguments.
- Exit codes.
- Standard output and error.
- Timeout records.
- Environment configuration.

This category should be distinguished from incorrect tool usage.

### F08 - Completion and Reporting Failure

**Definition:** The agent's final reported outcome does not accurately reflect the work completed.

Potential symptoms:

- Reporting success without completing the task.
- Claiming tests passed when they were not executed.
- Providing an inaccurate completion summary.
- Terminating without a meaningful final response.
- Reporting changes that are absent from the workspace.

Example:

The agent claims that the pagination bug is fixed, but the implementation remains unchanged.

Evidence:

- Final agent response.
- Workspace state.
- Execution history.
- Evaluation results.

## 4. Evaluation Outcome Categories

The following outcomes describe evaluation observations rather than agent failure causes.

| Outcome    | Meaning                                                        |
| ---------- | -------------------------------------------------------------- |
| PASS       | Test assertion succeeded                                       |
| FAIL       | Test assertion did not succeed                                 |
| ERROR      | Test execution encountered an error                            |
| SKIP       | Test was not executed                                          |
| INCOMPLETE | Agent did not report successful completion                     |
| BLOCKED    | Execution could not proceed because of an execution constraint |

These outcomes must not be conflated with the primary failure taxonomy.

For example, an execution error is an outcome. It may be associated with F07, F04, or another category depending on the evidence.

## 5. Primary and Contributing Failure Classification

Where multiple categories are observed, use the following classification structure.

**Primary failure:** The most directly supported category explaining the unsuccessful outcome.

**Contributing failure:** An additional observed category that materially affected the result.

**Undetermined:** The available evidence does not support a defensible classification.

Example:

An agent misunderstands a requirement, implements an incorrect algorithm, and does not execute the available tests.

Possible classification:

- Primary: F01 - Task Understanding Failure.
- Contributing: F05 - Implementation Failure.
- Contributing: F06 - Validation Failure.

This classification is illustrative. Actual attribution requires inspection of the execution evidence.

## 6. Failure Evidence Record

For future structured failure analysis, use the following conceptual record:

| Field                   | Description                                |
| ----------------------- | ------------------------------------------ |
| Run ID                  | Unique benchmark execution identifier      |
| Task ID                 | Benchmark task identifier                  |
| Failure ID              | Unique failure record identifier           |
| Primary category        | Main observed failure category             |
| Contributing categories | Additional supported categories            |
| Evidence                | Relevant actions, outputs, or test results |
| Evaluation outcome      | Associated evaluation result               |
| Impact                  | Requirements or behaviors affected         |
| Confidence              | Confidence in the classification           |
| Attribution             | Observed, inferred, or undetermined        |

Confidence should be based on available evidence rather than subjective impressions of agent intelligence.

## 7. Failure Analysis Examples

### Example 1 - Incorrect boundary handling

Scenario:

An agent implements pagination but fails when the number of items is not divisible by the page size.

Observed evidence:

- Incorrect total-page calculation.
- Hidden boundary test failure.

Possible classification:

- F05 - Implementation Failure.

### Example 2 - Incorrect repository investigation

Scenario:

An agent changes an unrelated response-formatting function instead of investigating the pagination logic.

Observed evidence:

- Original implementation.
- Agent file inspection history.
- Unrelated code modification.

Possible classification:

- F02 - Repository Understanding Failure.
- F03 - Planning and Decomposition Failure, if supported by the action history.

### Example 3 - Ineffective validation

Scenario:

An agent executes tests, receives a failure, and reports successful completion without addressing it.

Observed evidence:

- Test failure output.
- No corrective change.
- Final success response.

Possible classification:

- F06 - Validation Failure.
- F08 - Completion and Reporting Failure.

### Example 4 - Environment interruption

Scenario:

A valid command fails because the Python subprocess cannot initialize.

Observed evidence:

- Valid command arguments.
- Environment-related error.
- No evidence of incorrect agent command construction.

Possible classification:

- F07 - Execution and Environment Failure.

## 8. Relationship with Benchmark Scoring

Failure categories are diagnostic information.

They do not independently modify the current benchmark score.

The current scoring engine calculates test accuracy using:

\[
Score = \frac{P}{P + F + E} \times 100
\]

Where:

- P = Passed tests.
- F = Failed tests.
- E = Execution errors.

Benchmark success also depends on agent completion, visible test success, hidden test success, and the presence of at least one executed test.

Failure classifications should be reported alongside evaluation outcomes, not substituted for them.

## 9. Current Implementation Status

The current project includes a failure analysis component that processes agent completion and visible and hidden evaluation outcomes.

However, the existence of this component does not establish that all eight categories defined in this document are automatically detected, recorded, or validated.

The taxonomy is a proposed analytical standard for future implementation and evaluation.

Before claiming automated failure classification, the project must implement and test:

1. Explicit category definitions in code.
2. Evidence extraction rules.
3. Primary and contributing category assignment.
4. Structured failure records.
5. Classification validation.
6. Consistent reporting.
7. Evaluation of classification reliability.

Until then, this taxonomy should be treated as a documentation-level framework.

## 10. Future Research Directions

Potential research directions include:

- Measuring the distribution of agent failure categories.
- Comparing failure patterns across model configurations.
- Investigating relationships between tool-use behavior and task success.
- Studying how visible feedback affects subsequent agent actions.
- Measuring recurring implementation and validation failures.
- Evaluating the consistency of human or automated failure classification.

These investigations require actual benchmark observations and a documented classification procedure.

## 11. Research Integrity

Failure categories must be assigned based on evidence.

A test failure does not establish a particular reasoning defect.

A successful run does not establish that the agent used an optimal strategy.

Failure analysis must distinguish observed behavior from inferred causes and must preserve uncertainty when evidence is insufficient.

---

**End of Failure Taxonomy v1.0-draft**
