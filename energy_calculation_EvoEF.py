#!/usr/bin/env python 
# Copyright 2021 Mehdi Koşaca, Ezgi Karaca
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import pandas as pd

class EvoEF():
	def __init__(self,pdb_file,chain_id,algorithm):
		self.pdb = pdb_file[:-4]
		self.structure = pdb_file
		self.chain_id = chain_id
		self.algorithm = algorithm
		self.mutations = pd.read_table("{}_chain_{}_mutation_list".format(self.pdb,self.chain_id), header = None)
		self.scoresfile = pd.read_table("heatmap_mutation_list",sep = " ", header = None)
	def Preparing(self):
		single_chain = open("chain_{}.pdb".format(self.chain_id),"w")
		with open("{}.pdb".format(self.pdb),"r") as pdb:
			for line in pdb:
				if line[:4] == "ATOM":
					if line[21] == self.chain_id:
						print(line,file=single_chain,end="")
		single_chain.close()
		os.mkdir("{}_chain_{}_{}_output/mutation_models".format(self.pdb,self.chain_id,self.algorithm))
	def BuildMutation(self):
		os.system("./EvoEF --command=RepairStructure --pdb={}".format(self.structure))
		os.system("./EvoEF --command=RepairStructure --pdb=chain_{}.pdb".format(self.chain_id))
		os.rename("{}_chain_{}_mutation_list".format(self.pdb,self.chain_id),"individual_list.txt")
		os.system("./EvoEF --command=BuildMutant --pdb={}_Repair.pdb --mutant_file=individual_list.txt".format(self.pdb))
		os.system("./EvoEF --command=BuildMutant --pdb=chain_{}_Repair.pdb --mutant_file=individual_list.txt".format(self.chain_id))
		MutantEvoEFScores = []
		WTEvoEFScores = []
		StabilityMutantScores = []
		StabilityWTScores = []
		DDGBinding = []
		DDGStability = []
		os.system("./EvoEF --command=ComputeBinding --pdb={}_Repair.pdb > WT_CB.fxout".format(self.pdb))
		os.system("./EvoEF --command=ComputeStability --pdb=chain_{}_Repair.pdb > WT_CS.fxout".format(self.chain_id))
		for i in range(1,len(self.mutations)+1):
			if i < 10:
				os.system("./EvoEF --command=ComputeBinding --pdb={}_Repair_Model_000{}.pdb > Interaction_{}_Repair_{}_CB.fxout".format(self.pdb,i,self.pdb,i))
				os.system("./EvoEF --command=ComputeStability --pdb=chain_{}_Repair_Model_000{}.pdb > chain_{}_Repair_{}_0_CS.fxout".format(self.chain_id,i,self.chain_id,i))
				os.rename("{}_Repair_Model_000{}.pdb".format(self.pdb,i), "{}_Repair_Model_{}.pdb".format(self.pdb,self.mutations[0][i-1][:-1]))
				shutil.move("{}_Repair_Model_{}.pdb".format(self.pdb,self.mutations[0][i-1][:-1]), "{}_chain_{}_{}_output/mutation_models".format(self.pdb,self.chain_id,self.algorithm))
			elif 9 < i < 100:
				os.system("./EvoEF --command=ComputeBinding --pdb={}_Repair_Model_00{}.pdb > Interaction_{}_Repair_{}_CB.fxout".format(self.pdb,i,self.pdb,i))
				os.system("./EvoEF --command=ComputeStability --pdb=chain_{}_Repair_Model_00{}.pdb > chain_{}_Repair_{}_0_CS.fxout".format(self.chain_id,i,self.chain_id,i))
				os.rename("{}_Repair_Model_00{}.pdb".format(self.pdb,i), "{}_Repair_Model_{}.pdb".format(self.pdb,self.mutations[0][i-1][:-1]))
				shutil.move("{}_Repair_Model_{}.pdb".format(self.pdb,self.mutations[0][i-1][:-1]), "{}_chain_{}_{}_output/mutation_models".format(self.pdb,self.chain_id,self.algorithm))
			elif 99 < i < 1000:
				os.system("./EvoEF --command=ComputeBinding --pdb={}_Repair_Model_0{}.pdb > Interaction_{}_Repair_{}_CB.fxout".format(self.pdb,i,self.pdb,i))
				os.system("./EvoEF --command=ComputeStability --pdb=chain_{}_Repair_Model_0{}.pdb > chain_{}_Repair_{}_0_CS.fxout".format(self.chain_id,i,self.chain_id,i))
				os.rename("{}_Repair_Model_0{}.pdb".format(self.pdb,i), "{}_Repair_Model_{}.pdb".format(self.pdb,self.mutations[0][i-1][:-1]))
				shutil.move("{}_Repair_Model_{}.pdb".format(self.pdb,self.mutations[0][i-1][:-1]), "{}_chain_{}_{}_output/mutation_models".format(self.pdb,self.chain_id,self.algorithm))
			elif 999 < i < 10000:
				os.system("./EvoEF --command=ComputeBinding --pdb={}_Repair_Model_{}.pdb > Interaction_{}_Repair_{}_CB.fxout".format(self.pdb,i,self.pdb,i))
				os.system("./EvoEF --command=ComputeStability --pdb=chain_{}_Repair_Model_{}.pdb > chain_{}_Repair_{}_0_CS.fxout".format(self.chain_id,i,self.chain_id,i))
				os.rename("{}_Repair_Model_{}.pdb".format(self.pdb,i), "{}_Repair_Model_{}.pdb".format(self.pdb,self.mutations[0][i-1][:-1]))
				shutil.move("{}_Repair_Model_{}.pdb".format(self.pdb,self.mutations[0][i-1][:-1]), "{}_chain_{}_{}_output/mutation_models".format(self.pdb,self.chain_id,self.algorithm))
			with open("Interaction_{}_Repair_{}_CB.fxout".format(self.pdb,i)) as scoresfile:
				for line in scoresfile:
					if line[:23] == "Total                 =":
						MutantEvoEFScores.append(float(line[37:43]))
			with open("WT_CB.fxout") as wtbinding:
				for line in wtbinding:
					if line[:23] == "Total                 =":
						WTEvoEFScores.append(float(line[37:43]))
			with open("chain_{}_Repair_{}_0_CS.fxout".format(self.chain_id,i)) as stabilityscore:
				for line in stabilityscore:
					if line[:23] == "Total                 =":
						StabilityMutantScores.append(float(line[37:43]))
			with open("WT_CS.fxout") as wtstability:
				for line in wtstability:
					if line[:23] == "Total                 =":
						StabilityWTScores.append(float(line[37:43]))
			DDGBinding.append(MutantEvoEFScores[i-1] - WTEvoEFScores[i-1])
			DDGStability.append(StabilityMutantScores[i-1] - StabilityWTScores[i-1])
			DDGBindingFormatted = [round(num,2) for num in DDGBinding]
			DDGStabilityFormatted = [round(num,2) for num in DDGStability]
		self.scoresfile["{}_WT_Scores".format(self.algorithm)] = WTEvoEFScores
		self.scoresfile["{}_Mutant_Scores".format(self.algorithm)] = MutantEvoEFScores
		self.scoresfile["Stability_Mutant_Scores"] = StabilityMutantScores
		self.scoresfile["Stability_WT_Scores"] = StabilityWTScores
		self.scoresfile["DDG_{}_Scores".format(self.algorithm)] = DDGBindingFormatted
		self.scoresfile["DDG_Stability_Scores"] = DDGStabilityFormatted
		self.scoresfile.rename(columns={0:"Positions",1:"Mutations"},inplace=True)
		self.scoresfile.to_csv("{}_proton_scores_v1".format(self.pdb), index=False, sep = " ")
		os.system("sort -k1.2n {}_proton_scores_v1 > {}_chain_{}_proton_scores".format(self.pdb,self.pdb,self.chain_id))
		os.remove("{}_proton_scores_v1".format(self.pdb))
		os.rename("individual_list.txt", "{}_chain_{}_mutation_list".format(self.pdb,self.chain_id))
		os.system("rm *.fxout")
		
def main_EvoEF(pdb_file,chain_id,algorithm):
	f = EvoEF(pdb_file,chain_id,algorithm)
	f.Preparing()
	f.BuildMutation()


