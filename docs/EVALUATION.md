# AI-Agent-Bench: Evaluation Protocol

**Version:** 1.0-draft
**Status:** Initial evaluation specification
**Implementation scope:** Tests-based evaluation

## 1. Purpose

This document defines the evaluation protocol used by AI-Agent-Bench to assess the outcomes of LLM-powered software engineering agents.

The evaluation process verifies agent-generated changes against predefined functional requirements using independently executed visible and hidden tests.

The evaluator does not accept an agent's self-reported completion as proof of correctness.

The protocol describes the current implementation and distinguishes implemented evaluation capabilities from proposed future extensions.

## 2. Evaluation Architecture

The evaluation pipeline consists of the following components:

1. Benchmark task loader.
2. Task validator.
3. Workspace builder.
4. Agent runtime.
5. Command execution infrastructure.
6. Visible test evaluator.
7. Hidden test evaluator.
8. Scoring engine.
9. Failure analyzer.
10. Result storage and reporting.

The orchestrator coordinates these components.

Evaluation takes place after the agent has stopped executing.

## 3. Evaluation Lifecycle

A benchmark execution follows this sequence:

### Stage 1 - Task loading

The task loader retrieves the selected task specification.

The task validator checks the task assets and configuration.

Unsupported evaluation types are rejected. The current orchestrator supports tests-based evaluation only.

### Stage 2 - Workspace preparation

The workspace builder creates a task-specific workspace containing the permitted starter files and visible tests.

Hidden tests and reference implementation files are not intentionally copied into the normal agent workspace.

### Stage 3 - Agent execution

The agent receives the task instructions and available tool descriptions.

It interacts with the workspace through the registered tools, subject to configured execution limits.

The agent's completion status and execution history are retained for subsequent analysis.

### Stage 4 - Visible evaluation

After agent execution stops, the visible test evaluator executes the visible tests against the agent-modified workspace.

The evaluator records the resulting test outcomes.

### Stage 5 - Hidden evaluation

The hidden test evaluator independently executes the hidden tests against the same agent-modified workspace.

Hidden tests are intended to evaluate additional functional requirements without directly exposing their contents to the agent.

### Stage 6 - Score calculation

The scoring engine calculates the test score and determines whether the benchmark's success criteria have been satisfied.

### Stage 7 - Failure analysis

The failure analyzer examines the agent completion status and visible and hidden evaluation outcomes.

### Stage 8 - Result persistence

The result storage component saves the structured benchmark result.

The reporting component generates a Markdown report.

## 4. Visible Test Evaluation

Visible tests provide executable feedback on expected behavior.

They are available to the agent through the normal benchmark workspace.

The visible evaluator records:

- Passed tests.
- Failed tests.
- Execution errors.
- Skipped tests.
- Evaluation execution status.
- Relevant test output.

Visible tests help assess whether the agent has implemented the behavior demonstrated by the publicly available acceptance tests.

Passing visible tests alone does not establish complete task correctness.

## 5. Hidden Test Evaluation

Hidden tests evaluate additional functional requirements and edge cases.

They are stored separately from the agent's normal workspace.

The hidden evaluator executes them after agent execution has stopped.

Hidden tests should:

- Verify documented task requirements.
- Cover meaningful cases not adequately represented by visible tests.
- Avoid undocumented implementation assumptions.
- Produce deterministic outcomes.
- Be reviewed against the reference implementation.

The separation of hidden tests reduces direct test exposure. It does not provide a security guarantee against malicious code executing with host-user permissions.

## 6. Evaluation Independence

The evaluator operates after agent execution has stopped.

Visible and hidden evaluation results are not added to the agent's action history or prompts.

This establishes procedural separation between agent interaction and evaluation feedback.

However, the current architecture does not provide OS-level isolation between agent-generated code and evaluator execution.

Agent-generated code can potentially modify files in the workspace that are subsequently used by the evaluator.

Consequently, procedural separation must not be confused with complete evaluator integrity or security isolation.

## 7. Scoring Methodology

### 7.1 Test score

The current scoring engine calculates the score using:

\[
Score = \frac{P}{P + F + E} \times 100
\]

Where:

- \(P\) = Number of passed tests.
- \(F\) = Number of failed tests.
- \(E\) = Number of tests resulting in execution errors.

Skipped tests are excluded from the denominator.

The score represents the percentage of executed, non-skipped tests that passed.

### 7.2 Score interpretation

| Score             | Interpretation            |
| ----------------- | ------------------------- |
| 100               | All counted tests passed  |
| Between 0 and 100 | Some counted tests passed |
| 0                 | No counted tests passed   |

A score of 100 does not independently establish that the agent completed the task correctly. Agent completion and the benchmark's other success conditions must also be considered.

If no tests are executed, the result must not be interpreted as evidence of success.

### 7.3 Visible and hidden results

Visible and hidden evaluation outcomes are retained separately.

The benchmark should report both outcomes alongside the aggregate score.

This distinction helps identify agents that perform well against exposed tests but fail additional hidden requirements.

The score must be interpreted in the context of the executed test suite. Different test suites may have different numbers of tests and different coverage.

## 8. Benchmark Pass Criteria

A benchmark run is considered passed only when all the following conditions are satisfied:

1. The agent reports successful completion.
2. Visible tests pass.
3. Hidden tests pass.
4. At least one test has been executed.

The benchmark pass result is therefore stricter than the aggregate test score.

An agent that passes all visible tests but fails a hidden test does not pass the benchmark.

An agent that reports completion but fails functional evaluation does not pass the benchmark.

An agent that produces a high score but does not satisfy the completion criteria does not pass the benchmark.

## 9. Failure and Error Interpretation

Evaluation outcomes should be interpreted separately.

### Passed test

The tested behavior satisfied the corresponding assertion.

### Failed test

The implementation executed, but the tested behavior did not satisfy the expected result.

### Execution error

The test could not complete normally because of an execution or runtime error.

### Skipped test

The test was not included in the score denominator.

Skipped tests should be reviewed because extensive skipping can reduce the amount of behavior actually evaluated.

### Agent incomplete

The agent did not report successful completion.

Even when tests pass, an incomplete agent result does not satisfy the current benchmark pass criteria.

## 10. Failure Analysis

The failure analyzer examines:

- Agent completion status.
- Visible evaluation results.
- Hidden evaluation results.

Its purpose is to provide additional diagnostic information about benchmark outcomes.

Failure analysis should not be treated as a validated measure of reasoning quality or a definitive explanation of why an agent failed.

Where failure categories are used, they should be interpreted as diagnostic classifications rather than independently verified causal explanations.

## 11. Result Recording

Each benchmark run produces a structured result and a Markdown report.

The result record includes information such as:

- Task identifier and name.
- Task category and difficulty.
- Evaluation type.
- Agent provider and model.
- Agent completion status.
- Agent final message.
- Number of execution steps.
- Agent error information.
- Visible evaluation outcome.
- Hidden evaluation outcome.
- Aggregate score.
- Failure analysis.
- Benchmark pass status.
- Workspace location.

The run identifier supports distinguishing individual benchmark executions.

Results should be preserved so that later analysis can refer to the exact execution being evaluated.

## 12. Evaluation Reliability

A single benchmark run is not sufficient to establish stable model performance.

Model outputs may vary across executions.

For comparative experiments, each model-agent configuration should be evaluated over multiple independent trials.

Recommended reporting measures include:

- Number of trials.
- Mean test score.
- Standard deviation.
- Benchmark completion rate.
- Visible test pass rate.
- Hidden test pass rate.
- Execution error rate.
- Mean agent steps.
- Failure category distribution.

Repeated experiments should control or record model configuration, task version, agent implementation, tool configuration, and execution environment.

Statistical comparisons should only be made when the number and quality of observations justify them.

These repeated-trial and statistical capabilities are proposed extensions, not claims about the current implementation.

## 13. Evaluation Limitations

The current evaluation system has important limitations.

### 13.1 Functional correctness

The evaluator primarily measures functional correctness against predefined tests.

It does not comprehensively assess code readability, maintainability, architectural quality, performance, or long-term reliability.

### 13.2 Test coverage

The quality of evaluation depends on the quality and completeness of the task tests.

A passing test suite cannot establish correctness for behavior that the suite does not examine.

### 13.3 Evaluator integrity

The evaluator runs locally against an agent-modified workspace.

The current system does not provide OS-level isolation or tamper-proof evaluation infrastructure.

### 13.4 Statistical reliability

The current implementation does not establish statistically reliable comparative model rankings through repeated experimental trials.

### 13.5 Generalization

The current benchmark contains one substantive task.

Results cannot be generalized to all software engineering tasks or all LLM-powered agents.

## 14. Future Evaluation Improvements

The following improvements are potential future development directions:

1. Repeated-trial execution and aggregation.
2. More detailed execution traces.
3. Standardized failure classification.
4. Task-level coverage analysis.
5. Stronger evaluator isolation.
6. Reproducible experiment configuration.
7. Baseline model-agent comparisons.
8. Confidence intervals and appropriate statistical analysis.
9. Additional evaluation dimensions beyond functional correctness.

Each improvement should be implemented and tested before being described as an existing capability.

## 15. Research Integrity

Evaluation results must be traceable to actual benchmark executions.

Reports and research publications must distinguish:

- Test score from benchmark success.
- Task-level correctness from general agent capability.
- Diagnostic failure labels from verified causal explanations.
- Implemented features from proposed improvements.
- Engineering functionality from empirically validated research findings.

AI-Agent-Bench must not claim statistical significance, comprehensive agent evaluation, or secure execution without supporting evidence.

---

**End of Evaluation Protocol v1.0-draft**
