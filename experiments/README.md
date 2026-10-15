# ReviewWise — M2 Experiments

## Purpose

For M2, we tested whether Qwen2.5 (3B) could analyze multilingual café reviews and generate a weekly feedback report.

We used the same 10 fictional reviews in English, French and German for all three experiments.

## Requirements

- Python
- Ollama installed and running
- Qwen2.5 (3B)

Install the model:

```powershell
ollama pull qwen2.5:3b
```

Install the Python library:

```powershell
pip install ollama
```

## How to Run

Open a terminal in the main `reviewwise-ai` folder and run:

```powershell
python .\experiments\m2_experiment_1.py
python .\experiments\m2_experiment_2.py
python .\experiments\m2_experiment_3.py
```

## Results

Each experiment generates a weekly report.

- Experiment 1: `experiment_output_1.txt`
- Experiment 2: `experiment_output_2.txt`
- Experiment 3: `experiment_output_3.txt`

The results and mistakes found in each experiment are explained in `experiment_commentary.md`.

We chose the two-stage approach from Experiment 3 as the starting point for our MVP.