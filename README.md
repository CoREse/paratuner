# Parameter tuner

## Tune your parameter

Two modes:

Traversal Mode: Execute all possible parameters to achieve the best outcome.

Round Mode: Sequentially traverse each parameter until the result deteriorates, then randomize upon completion of the entire round before initiating a new round.

## Usage

You need to run bench.sh to obtain the result (a numerical score where higher values indicate better performance).

Import paratuner:
```
import sys
sys.path.append('PATH/TO/PARATUNER')
import tuner
```
To set parameter option:

```
Program="PATH/TO/PROGRAM/YOU/WANT/TO/TUNE"
Para=tuner.Para
Paras=[
    Para("-F","FixedValue"),
    Para("--ComplexPara","[[-10,101,10],[0,10.1,1]]"),#[[Start0,End0,Step1],[Start1,End1,Step1],...], produce like: "--ComplexPara -10,0"
    Para("--Range",(0,1.01,0.1)),#(Start, End, Step) traverse [Start,End)
    Para("FlagOrPositional",Type=2)
]
```

To set name, data path and bench script:
```
TestName="TESTNAME"
OutPath="data"
Bench="PATH/TO/bench.sh"
```

### Traversal Mode
```
tuner.runAllParas(Program,OutPath,TestName,Paras,Bench=Bench)
```

### Round Mode:
```
NRounders=1000
RandomSeed=0
tuner.tuner.runRounders(Program,OutPath,TestName,Paras,Bench,NRounders,RandomSeed,LooseRand=False,Mode=0)
```

To run:
```
python3 -u yourtunerscript.py > log.log 2>&1
```