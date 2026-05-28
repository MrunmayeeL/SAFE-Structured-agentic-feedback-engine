# SAFE: Structured Agentic Feedback for Localized LLM-Based Program Repair

> **Mrunmayee Limaye,Harshal Kolhe & Nidhi Paresh Lodha**  
> Department of Computer Science and Engineering & Department of Chemical Engineering
> Visvesvaraya National Institute of Technology, Nagpur, India

---

## Abstract

Large Language Models (LLMs) have recently shown strong capabilities in Automated Program Repair (APR). However, existing LLM-based repair systems still rely heavily on naive full-context prompting, where entire source files and raw execution logs are provided directly to the model. This introduces excessive prompt overhead, hallucinated code modifications, unstable iterative behavior, and poorly localized patches.

**SAFE (Structured Agentic Feedback Engine)** is a lightweight structured debugging and repair framework that decomposes repair into multiple stages: runtime feedback collection, traceback-guided localization, propagation-aware reasoning, strategy-guided repair planning, localized prompt construction, and iterative validation. Instead of exposing the model to complete source files, SAFE extracts only runtime-relevant code regions and augments repair prompts with structured propagation chains and debugging strategies.

Evaluated on the Python subset of the **QuixBugs** benchmark using **Qwen2.5-Coder** under local inference, SAFE significantly reduces prompt size and unnecessary code modifications while improving repair localization, syntax stability, and hallucination reduction.

---

## Architecture

```
Buggy Program
     │
     ▼
Program Execution & Error Detection
     │
     ▼
Localised Context Extraction
     │
     ▼
Structured Feedback Generator
  ├── Propagation-Aware Analysis
  ├── Error Classification
  └── Strategy Selection
     │
     ▼
LLM-Based Repair (Qwen2.5-Coder via Ollama)
     │
     ▼
Validation & Iterative Repair
     │
     ▼
Valid Working Program
```

### Core Modules (`src/safe/`)

| Module | Description |
|---|---|
| `executor.py` | Runs buggy programs against test suites in an isolated environment with timeout protection |
| `classifier.py` | Classifies runtime errors into categories (IndexError, LogicError, Timeout, etc.) |
| `analyzer.py` | Performs traceback-guided localization and AST-based propagation analysis |
| `strategy.py` | Selects repair strategies based on error categories |
| `fixer.py` | Constructs localized structured prompts and queries the LLM (Ollama) |
| `integrator.py` | Integrates generated patches back into the original program |

### Baseline (`src/baseline/`)

A naive full-context prompting system that supplies the complete source file + raw error to the LLM without localization or propagation reasoning.

---

## Repository Structure

```
SAFE-APR/
├── src/
│   ├── safe/                   # SAFE framework modules
│   │   ├── analyzer.py         # Context localization + propagation analysis
│   │   ├── classifier.py       # Error classification
│   │   ├── executor.py         # Isolated program execution
│   │   ├── fixer.py            # Localized LLM repair prompt + generation
│   │   ├── integrator.py       # Patch integration
│   │   └── strategy.py         # Repair strategy selection
│   ├── baseline/
│   │   └── fixer.py            # Naive full-context baseline
│   ├── loader.py               # QuixBugs dataset loader
│   ├── utils.py                # Shared utilities (diff, syntax check, hallucination detection)
│   ├── experiment_runner.py    # Full experiment pipeline (SAFE vs Baseline)
│   ├── analyze_results.py      # Results analysis
│   ├── results_analyzer.py     # Extended results analysis
│   └── plot_results.py         # Standalone plot generation
├── benchmarks/
│   └── QuixBugs/
│       ├── python_programs/    # Buggy Python implementations
│       ├── python_testcases/   # pytest test files
│       └── json_testcases/     # JSON test case data
├── experiments/                # Custom experiment scripts
├── results/
│   ├── graphs/                 # Generated evaluation plots
│   ├── logs/                   # Per-bug JSON logs (baseline + SAFE)
│   ├── examples/               # Qualitative patch comparisons
│   └── all_results.json        # Aggregated experiment results
├── main.py                     # Quick-start entry point
├── requirements.txt
└── .github/workflows/ci.yml
```

---

## Results

| Metric | Baseline | SAFE |
|---|---|---|
| Repair Success Rate | 28.0% | **32.0%** |
| Avg Prompt Size | Higher | **Significantly Lower** |
| Avg Changed Lines (successful fixes) | 14.4 | **9.1** |
| Syntax Validity Rate | 96.0% | **100.0%** |
| Hallucination Rate | Higher | **Lower** |

### Key Findings

- **Prompt Efficiency**: SAFE consistently reduced prompt size across all benchmark programs by restricting context to runtime-relevant execution regions only.
- **Patch Minimality**: SAFE generated smaller, more localized patches (avg 9.1 changed lines vs 14.4 for baseline on successful fixes).
- **Syntax Stability**: SAFE achieved 100% syntax validity vs 96% for baseline, eliminating malformed patch generation.
- **Hallucination Reduction**: Structured prompting prevented fabricated helper functions, unsupported imports, and unrelated structural rewrites.

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- Qwen2.5-Coder model pulled via Ollama

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/SAFE-APR.git
cd SAFE-APR
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Pull the repair model

```bash
ollama pull qwen2.5-coder:1.5b
```

Make sure Ollama is running:
```bash
ollama serve
```

### 4. Run a quick demo

```bash
python main.py
```

### 5. Run the full experiment (SAFE vs Baseline on QuixBugs)

```bash
cd src
python experiment_runner.py
```

Results will be saved to `results/logs/`, `results/graphs/`, and `results/all_results.json`.

---

## Configuration

Edit the constants at the top of `src/experiment_runner.py`:

```python
DATASET_PATH = "benchmarks/QuixBugs"   # Path to QuixBugs
MAX_ITERATIONS = 5                       # Max repair iterations per bug
BUG_LIMIT = 25                           # Number of bugs to evaluate
```

The LLM endpoint is configured in `src/safe/fixer.py`:

```python
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:1.5b"
```

---

## How SAFE Works

### 1. Runtime Feedback Collection
SAFE executes the buggy program `P` with test suite `T` to collect runtime feedback `R = Execute(P, T)`, including assertion failures, tracebacks, and timeout events.

### 2. Context Localization
Rather than supplying the full source file, SAFE uses traceback-guided localization:
```
L = Localize(P, R)
```
Only runtime-relevant code regions near the failing line are extracted using sliding windows.

### 3. Propagation-Aware Analysis
SAFE traces variable assignments and dependency flows upstream from the failure point. For example:
```
value[0]  ←  process(data)  ←  data  ←  get_data()  ←  None
```
This identifies the root-cause origin rather than just patching the surfaced symptom.

### 4. Structured Prompt Construction
```
PromptSAFE = { L, R, G, S }
```
where `L` = localized context, `R` = runtime feedback, `G` = propagation chain, `S` = strategy instructions.

### 5. Iterative Validation
```
P(t+1) = Integrate(P(t), P')
R(t+1) = Execute(P(t+1), T)
```
The loop continues until tests pass or the iteration budget is exhausted.

---

## Benchmark: QuixBugs

QuixBugs contains buggy Python implementations of 40 classical algorithmic problems with associated test suites. Bug categories include logical errors, boundary violations, indexing failures, recursion defects, null-reference propagation, infinite loops, and syntax bugs.

The benchmark is included as a submodule under `benchmarks/QuixBugs/`. Original source: [QuixBugs GitHub](https://github.com/jkoppel/quixbugs).

---

### References

1. Weimer et al., "GenProg: A generic method for automatic software repair," ICSE 2009.
2. Liu et al., "TBar: Revisiting template-based automated program repair," ISSTA 2019.
3. Chen & Monperrus, "SequenceR: Sequence-to-sequence learning for end-to-end program repair," ICSE 2019.
4. Lu et al., "Recoder: Transformer-based program repair," ICSE 2021.
5. Xia et al., "AlphaRepair: Program repair with large language models," arXiv 2023.
6. Kong et al., "ContrastRepair: Enhancing conversation-based APR via contrastive test case pairs," TOSEM 2025.
7. Zhang et al., "AutoCodeRover: Autonomous program improvement," ISSTA 2024.
8. Yang et al., "SWE-agent: Agent-computer interfaces enable automated software engineering," arXiv 2024.
9. Lin et al., "QuixBugs: A benchmark of algorithmic programs with bugs," 2017.

---

## License

This project is released for academic research purposes. The QuixBugs benchmark is subject to its own license — see `benchmarks/QuixBugs/LICENSE`.
