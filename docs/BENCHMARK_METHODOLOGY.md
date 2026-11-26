# AI-Agent-Bench: Benchmark Methodology

**Version:** 1.0-draft
**Status:** Initial engineering methodology - pending empirical validation

## 1. Purpose

AI-Agent-Bench is a framework for evaluating the ability of LLM-powered agents to complete software engineering tasks through iterative interaction with a controlled set of development tools.

The benchmark evaluates task completion using independently executed tests rather than relying exclusively on the agent's self-reported success.

Its initial implementation focuses on Python software engineering tasks.

The benchmark is designed to support systematic investigation of:

- Agent task completion.
- Tool-use effectiveness.
- Code correctness.
- Compliance with task requirements.
- Failure patterns during software engineering tasks.
- Differences in performance across agents and model configurations.

These are intended evaluation dimensions. Their empirical validity and measurement reliability have not yet been established.

## 2. Research Objective

The primary research objective is:

**How reliably can LLM-powered agents complete structured software engineering tasks when evaluated against independently executed functional requirements?**

The initial benchmark investigates this question through executable programming tasks with predefined starter code, task instructions, visible tests, and hidden tests.

Future experiments may investigate how agent architecture, model selection, tool availability, and execution constraints influence task performance.

## 3. Benchmark Scope

### 3.1 Current scope

The current implementation supports:

- Python-based software engineering tasks.
- YAML-defined benchmark task specifications.
- Workspace creation from starter code.
- LLM-powered agent execution.
- Iterative tool interaction.
- Command execution through an allowlisted command interface.
- Visible test evaluation.
- Hidden test evaluation.
- Automated scoring.
- Failure analysis.
- JSON result storage.
- Markdown result reports.

### 3.2 Current limitations

The current implementation does not establish:

- General-purpose agent intelligence.
- Performance across all software engineering domains.
- Security against malicious agent-generated code.
- Reproducibility across different operating systems.
- Statistical significance of model comparisons.
- Generalization from one benchmark task to broader programming ability.

The benchmark currently has one substantive task, PB-SWE-001. Consequently, its results must not be interpreted as representative of general software engineering agent performance.

## 4. Benchmark Task Structure

Each benchmark task is defined through a structured task directory.

A task may contain:

- `task.yaml`: Task metadata, instructions, environment configuration, and evaluation configuration.
- `starter/`: Initial code supplied to the agent.
- `visible_tests/`: Tests available to the agent during development.
- `hidden_tests/`: Tests withheld from the agent.
- `reference/`: Reference implementation used for benchmark development and verification.

The workspace builder copies the permitted starter files and visible tests into the agent workspace.

Hidden tests and reference implementation files are not intentionally exposed through the normal agent workspace.

This separation reduces direct test exposure but does not establish strong isolation against a malicious process with access to the host filesystem.

## 5. Task Execution Protocol

A benchmark run follows these stages:

1. Load the benchmark task.
2. Validate the task specification and required assets.
3. Resolve trusted visible and hidden test directories.
4. Create a task-specific execution workspace.
5. Initialize the agent tool registry.
6. Construct the agent request.
7. Execute the agent within the configured step limit.
8. Stop agent execution.
9. Execute visible tests independently.
10. Execute hidden tests independently.
11. Calculate the benchmark score.
12. Analyze failures.
13. Store structured results.
14. Generate a Markdown report.

The evaluator runs after agent execution has stopped. Evaluation outputs are not fed back into the agent's interaction history.

## 6. Evaluation Methodology

### 6.1 Functional evaluation

The current implementation uses pytest-based functional evaluation.

Visible and hidden tests are executed separately against the agent-modified workspace.

The evaluation records test outcomes, including:

- Passed tests.
- Failed tests.
- Execution errors.
- Skipped tests.
- Execution status and relevant output.

### 6.2 Visible tests

Visible tests provide the agent with feedback about expected functionality.

They allow the agent to inspect requirements through executable examples and validate its implementation during task execution.

### 6.3 Hidden tests

Hidden tests evaluate requirements that are not directly exposed through the agent's workspace.

They are intended to assess whether the implementation satisfies additional functional constraints rather than merely reproducing visible test examples.

Hidden-test separation is an evaluation design measure, not a security boundary.

### 6.4 Evaluation independence

The evaluator executes after the agent has completed or stopped.

The evaluation results are not included in the agent's prompt or action history.

This establishes procedural separation between agent interaction and test evaluation, although the current local execution architecture does not provide OS-level isolation.

## 7. Scoring Methodology

The current scoring engine calculates test accuracy using:

\[
Score = \frac{P}{P + F + E} \times 100
\]

Where:

- \(P\) = Passed tests.
- \(F\) = Failed tests.
- \(E\) = Tests resulting in execution errors.

Skipped tests are excluded from the denominator.

If no tests are executed, the score must not be interpreted as evidence of successful task completion.

### 7.1 Benchmark pass criteria

A benchmark run is considered successful only when:

- The agent reports completion.
- Visible tests pass.
- Hidden tests pass.
- At least one test has been executed.

The aggregate test score alone does not determine benchmark success.

### 7.2 Score interpretation

The score represents the proportion of executed, non-skipped tests that passed.

It is not a direct measure of reasoning quality, software engineering expertise, efficiency, or general intelligence.

Results should be interpreted alongside the visible-test outcomes, hidden-test outcomes, agent completion status, and failure analysis.

## 8. Agent Execution Constraints

The agent operates under configurable constraints, including:

- Maximum interaction steps.
- Tool availability.
- Command execution timeout.
- Workspace boundaries for normal tool operations.
- Output size limits.

The command runner uses an executable allowlist, subprocess execution without shell invocation, execution timeouts, and output truncation.

These mechanisms constrain the normal tool interface but do not constitute an OS-level sandbox.

Agent-generated Python code can potentially access host resources available to the executing user.

Real-model execution is therefore disabled by default and requires explicit local execution consent.

## 9. Experimental Reproducibility

A benchmark result should record sufficient information to identify the experiment, including:

- Task identifier.
- Run identifier.
- Model identifier.
- Provider.
- Agent completion status.
- Number of agent steps.
- Visible evaluation results.
- Hidden evaluation results.
- Aggregate score.
- Failure analysis.
- Execution artifacts and report location.

For meaningful comparisons, future experiments should additionally standardize:

- Model version and configuration.
- Agent implementation and system instructions.
- Tool definitions and permissions.
- Task version.
- Execution environment.
- Evaluation configuration.
- Run count and aggregation method.

The current implementation does not yet establish statistically reliable comparisons through repeated trials.

## 10. Reliability and Statistical Evaluation

A single successful or unsuccessful run is insufficient to establish stable agent performance.

Future comparative experiments should execute each model-agent configuration across multiple trials.

Recommended reporting measures include:

- Mean task score.
- Standard deviation.
- Task completion rate.
- Visible test pass rate.
- Hidden test pass rate.
- Execution failure rate.
- Mean agent steps.
- Failure category distribution.

Confidence intervals and appropriate statistical comparisons should be introduced when sufficient independent observations are available.

Repeated runs must account for stochastic model outputs and other sources of experimental variation.

## 11. Threats to Validity

### 11.1 Construct validity

Passing predefined tests may not capture all dimensions of software engineering quality.

The current benchmark primarily measures functional correctness against specified test cases.

It does not comprehensively measure maintainability, readability, architectural quality, or long-term software reliability.

### 11.2 Internal validity

Differences in model behavior may be influenced by nondeterministic outputs, execution environments, provider changes, and agent configuration.

These factors must be controlled or recorded in comparative experiments.

### 11.3 External validity

A single Python programming task cannot establish performance across the broader software engineering domain.

Additional tasks covering different programming concepts, complexity levels, and problem types are necessary.

### 11.4 Evaluation validity

Hidden tests can improve resistance to direct test memorization, but their quality determines how effectively they distinguish correct implementations from superficial solutions.

Test coverage, edge cases, and reference implementation verification require ongoing review.

### 11.5 Security validity

The current execution environment is not an OS-level sandbox.

Workspace restrictions, command allowlists, and environment filtering do not prevent arbitrary Python code from accessing host resources.

The benchmark must not be represented as secure against malicious agent-generated code.

## 12. Current Benchmark Maturity

The current release is an engineering MVP with an initial executable benchmark task.

Its implementation demonstrates a working evaluation pipeline, but the benchmark has not yet undergone sufficient empirical validation to support broad research claims.

The next development stages should prioritize:

1. Additional high-quality benchmark tasks.
2. Task difficulty and category definitions.
3. Evaluation coverage and test-quality review.
4. Repeated experimental trials.
5. Baseline model-agent experiments.
6. Reproducibility documentation.
7. Independent review of benchmark validity.

## 13. Research Integrity

All reported results must be traceable to actual benchmark executions.

The benchmark must distinguish between:

- Implemented functionality.
- Tested functionality.
- Experimentally validated findings.
- Proposed future capabilities.

No benchmark performance, security guarantee, statistical significance, or generalization claim should be made without supporting evidence.

---

**End of Benchmark Methodology v1.0-draft**
