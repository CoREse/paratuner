import numpy as np
import json

def getSNOpts(Name, Ranges, Result=[], ri=0):
    if ri==len(Ranges):
        return Result
    Results=[]
    if ri==0:
        for V in np.arange(*Ranges[ri]):
            Result=[str(Name),str(V)]
            if ri==len(Ranges)-1:
                Results.append(getSNOpts(Name,Ranges,Result,ri+1))
            else:
                Results+=getSNOpts(Name,Ranges,Result,ri+1)
        return Results
    for V in np.arange(*Ranges[ri]):
        CResult=Result.copy()
        CResult[1]+=","+str(V)
        if ri==len(Ranges)-1:
            Results.append(getSNOpts(Name,Ranges,CResult,ri+1))
        else:
            Results+=getSNOpts(Name,Ranges,CResult,ri+1)
    return Results

class Para:
    def __init__(self, Name, Range=None, Value=None, Type=None):#0: Numeric, 1: String, 2: Flag, 3: String numeric, 4: Joint Paras
        self.Name=Name
        if Type==None:
            if Range!=None:
                Type=0
                if Range[0]=="[":#"[[start,end,gap],...]""
                    Type=3
            elif Value==None:
                Type=2
            elif type(Value)==list:
                Type=4
            else:
                Type=1
        self.Value=Value
        self.Range=Range
        self.Type=Type
    def toOpts(self):
        if self.Type==2:
            return [[str(self.Name)]]
        if self.Type==1:
            return [[str(self.Name), str(self.Value)]]
        Result=[]
        if self.Type==0:
            if self.Range!=None:
                for V in np.arange(*self.Range):
                    Result.append([str(self.Name), str(V)])
        elif self.Type==3:
            Ranges=json.loads(self.Range)
            Result=getSNOpts(self.Name,Ranges)
        elif self.Type==4:
            return [[str(self.Name), self.Value]]#Value is a list.
        return Result
    def __str__(self):
        if self.Type==2:
            return str(self.Name)
        if self.Type==1:
            return str(self.Name)+" "+str(self.Value)
        return str(self.Name)+" "+str(self.Range)

import subprocess
import os

def runAndBench(Program,OutPath,TestName,ParasOpt,Bench=None,Show=False,Mark=""):
    if OutPath=="":
        OutPath=TestName+"/"
    else:
        OutPath=OutPath+"/"+TestName+"/"
    if not os.path.exists(OutPath):
        os.mkdir(OutPath)
    Out=OutPath+TestName+".vcf"
    # Null=open("/dev/null","w")
    RunParas=[ParasOpt.copy()]
    # print("P9:",type(ParasOpt[9]))
    for i in range(len(ParasOpt)):
        NewRunParas=[]
        for j in range(len(RunParas)):
            if type(RunParas[j][i])==list:
                for k in range(len(RunParas[j][i])):
                    # print("k:",RunParas[j][:i][k])
                    if type(RunParas[j][i][k])==list:
                        NewRunParas.append(RunParas[j][:i]+RunParas[j][i][k]+RunParas[j][i+1:])
                    else:
                        NewRunParas.append(RunParas[j][:i]+[RunParas[j][i][k]]+RunParas[j][i+1:])
                    # print("NewParas:",NewRunParas)
        if NewRunParas!=[]:
            RunParas=NewRunParas
    Result=0
    # print("RunParas:",RunParas)
    for i in range(len(RunParas)):
        Ps=RunParas[i]
        if Show:
            print("{[%s]}Running %s..."%(Mark," ".join([Program]+Ps)))
        OutFile=open(Out,"w")
        # print("Ps:",Ps)
        run=subprocess.Popen([Program]+Ps,stderr=subprocess.DEVNULL,stdout=OutFile)
        run.wait()
        OutFile.close()
        # Null.close()
        if Bench!=None:
            if type(Bench)!=list:
                run=subprocess.Popen(["bash",Bench,TestName],cwd=OutPath,stdout=subprocess.PIPE)
                output, error = run.communicate()
                BenchResult=output.decode()
                print(output.decode())
                Result+=float(BenchResult.splitlines()[-1])
            else:
                run=subprocess.Popen(["bash",Bench[i],TestName],cwd=OutPath,stdout=subprocess.PIPE)
                output, error = run.communicate()
                BenchResult=output.decode()
                print(output.decode())
                Result+=float(BenchResult.splitlines()[-1])
    return Result
    return None

BestResult=0
BestMark=""
# print("Tunning %s"%(" ".join([Program]+[str(p) for p in Paras])))
def runAllParas(Program,OutPath,TestName,Paras,ParasOpt=[], Bench=None,i=0, Mark=""):
    global BestResult
    global BestMark
    if i==len(Paras):
        print("Running %s...{[%s]}"%(" ".join([Program]+ParasOpt),Mark))
        Result=runAndBench(Program,OutPath,TestName,ParasOpt,Bench)
        print("[%s]Result:%s"%(Mark,Result))
        if (float(Result)>float(BestResult)):
            BestResult=float(Result)
            BestMark=Mark
        print("[%s]Best:%s"%(BestMark,BestResult))
        return ParasOpt
    for Opt in Paras[i].toOpts():
        NewMark=Mark
        if Paras[i].Type==0 or Paras[i].Type==3:
            if (Mark!=""):
                NewMark+=";"
            NewMark+=Opt[-1]
        runAllParas(Program, OutPath,TestName, Paras,ParasOpt+Opt, Bench,i+1, NewMark)
import random
#Mode=0: break when not go up, Mode=1: break when go down
#LooseRand=False: Randomize when index not change, True: when best not change
def runRounders(Program,OutPath,TestName,Paras,Bench,NRounders,Random=0,LooseRand=True,Mode=0,Start=None):#stop when result drop at each parameter, and repeat n times, bench should print a value at last line.
    ParasOpt=[]#Paras for running
    ParaOpts=[]#Opts for each para
    ParaOptsI=[]#current para index for opts
    Mark=""#for visual convenient
    if Random!=None:
        random.seed(Random)
    for i in range(len(Paras)):
        Opts=Paras[i].toOpts()
        ParaOpts.append(Opts)
        ParasOpt+=Opts[0]
        ParaOptsI.append(0)
    if Start!=None:
        ParasOpt=[]
        ParaOptsI=[]
        for i in range(len(Start)):
            ParasOpt+=Start[i]
            ParaOptsI.append(ParaOpts[i].index(Start[i]))
    LastResult=0
    BestResult=0
    BestResultMark=""
    LastRoundBestResultMark=None
    LastIndexes=None
    LastUnchanged=False
    print("Running rounders for %s rounds..."%(NRounders))
    for r in range(NRounders):
        print("Running round %s..."%(r))
        print("LastIndexes: %s, ParaOptsI: %s"%(LastIndexes,ParaOptsI))
        if Random!=None:
            if (LooseRand and (LastRoundBestResultMark!=None) and LastRoundBestResultMark==BestResultMark) or ((not LooseRand) and LastIndexes!=None and LastIndexes==ParaOptsI):
                print("No change for a round, randomizing...")
                ParasOpt=[]
                ParaOptsI=[]
                for i in range(len(Paras)):
                    Index=random.randint(0,len(ParaOpts[i])-1)
                    ParasOpt+=ParaOpts[i][Index]
                    ParaOptsI.append(Index)
        elif LastIndexes!=None and LastIndexes==ParaOptsI:
            print("No change, stop iteration.")
            break
        LastRoundBestResultMark=BestResultMark
        LastIndexes=ParaOptsI.copy()
        for i in range(len(Paras)):
            Opts=ParaOpts[i]
            Start=ParaOptsI[i]
            j=Start
            if LastUnchanged:
                j+=1
                if Start!=0 and j==len(Opts)-1:
                    j=0
            if len(Opts)<=1:
                continue
            LastUnchanged=True
            while j<len(Opts):
                #because the LastUnchanged flag, this may not be printed, that's normal
                print(i,j)
                # if len(Opts)==1:
                #     break
                NewParasOpt=[]
                for p in range(len(Paras)):
                    if (p==i):
                        NewParasOpt+=ParaOpts[p][j]
                    else:
                        NewParasOpt+=ParaOpts[p][ParaOptsI[p]]
                Mark=""
                for m in range(len(Paras)):
                    Index=ParaOptsI[m]
                    if (m==i):
                        Index=j
                    TOpts=ParaOpts[m]
                    if Paras[m].Type==0 or Paras[m].Type==3:
                        if (Mark!=""):
                            Mark+=";"
                        Mark+=TOpts[Index][-1]
                BenchResult=runAndBench(Program,OutPath,TestName,NewParasOpt,Bench,True,Mark)
                Result=BenchResult
                # Result=float(BenchResult.splitlines()[-1])
                if Result>BestResult:
                    BestResult=Result
                    BestResultMark=Mark
                print("CurrentResult: %s, LastResult: %s, BestResult: %s({%s})"%(Result,LastResult,BestResult,BestResultMark))
                if (Mode==0 and Result<=LastResult) or (Mode==1 and Result<LastResult):
                    break
                ParasOpt=NewParasOpt
                ParaOptsI[i]=j
                LastResult=Result
                LastUnchanged=False
                if Start!=0 and j==len(Opts)-1:
                    j=0
                else:
                    j+=1      

# runAllParas(Paras)