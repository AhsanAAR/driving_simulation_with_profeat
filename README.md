# Autonomous Driving Simulation with ProFeat

This project contains a ProFeat model that allows probabilistic model checking of a self-driving car scenario over a range of factors.

## Project Structure

| File | Description |
|------|-------------|
| `car.pm` | The pure PRISM model that the ProFeat model is based on. |
| `model.profeat` | The ProFeat model. |
| `props.props` | Property specifications: the minimum probability of crashing over the first 100 time-steps (stepped by 10), plus a sanity check that tries to crash the car within 10 steps. |
| `script.py` | Results consolidation script that compiles the results from one run of ProFeat into a single CSV table. |

## Prerequisites / Setup

This project requires two external tools, which should be placed in the same directory as `model.profeat`:

1. **ProFeat** – the tool used to run this project.
   https://wwwtcs.inf.tu-dresden.de/ALGI/PUB/ProFeat/

2. **PRISM model checker** – required as the underlying model checking backend.
   https://www.prismmodelchecker.org/download.php

## Running the Model

Once both tools are installed in the same directory as the model, run the following command from the terminal:

```bash
./profeat test.profeat props.props --prism-path="./prism" -r "results.csv" --export-log prism_log --one-by-one --prism-log
```

This produces one model per configuration and allows each configuration to be studied separately.
