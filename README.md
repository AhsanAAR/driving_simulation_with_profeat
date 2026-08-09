# Autonomous Driving Simulation with ProFeat
This project contains a ProFeat model that allows probabilistic model checking of a self-driving car scenario over a range of factors
- car.pm contains the pure PRISM model that the ProFeat model is based on.
- script.py contains a results consolidation script that compiles the results from one run of ProFeat into one csv table.
- model.profeat contains the ProFeat model.

## Prerequisites / Setup

This project requires two external tools, which should be placed in the same directory as `model.profeat`:

1. **ProFeat** – the tool used to run this project.
   https://wwwtcs.inf.tu-dresden.de/ALGI/PUB/ProFeat/

2. **PRISM model checker** – required as the underlying model checking backend.
   https://www.prismmodelchecker.org/download.php

Once both are installed in the same directory as the model, run the following command from the terminal:

```bash
./profeat test.profeat props.props --prism-path="./prism" -r "results.csv" --export-log prism_log --one-by-one --prism-log
```

This produces one model per configuration and allows each configuration to be studied separately.
