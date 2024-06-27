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
import numpy as np
import pandas as pd

class Alerts():	
	def __init__(self,pdb_file,chn_1,chn_2,selected_chain,pssm,cut_off):
		self.pssm = pssm
		self.pdb_file = pdb_file
		self.pdb = pdb_file[:-4]
		self.chn_1 = chn_1
		self.chn_2 = chn_2
		self.selected_chain = selected_chain
		self.chain_ids = []
		self.chains = []
		self.position = []
		self.cut_off = cut_off
		self.chain_1 = []
		self.chain_2 = []
		self.chain_1_coord = []
		self.chain_2_coord = []

	def Chain_Alert(self):
		with open("{}".format(self.pdb_file), "r") as pdbfile:
			for line in pdbfile:
				if line[:4] == "ATOM":
					self.chains.append(line[21])
					if self.pssm != "":
						if line[21] == self.selected_chain:
							psp = line[22:26]
							self.position.append(int(psp))
		chain_ids = np.unique(self.chains)
		if self.chn_1 in chain_ids and self.chn_2 in chain_ids:
			return True
		else:
			os.remove(os.path.join(self.pdb_file))
			if self.pssm != "":
				os.remove(os.path.join(self.pssm))
			return False
		
	def Chain_on_Alert(self):
		if self.selected_chain == "on":
			os.remove(os.path.join(self.pdb_file))
			if self.pssm != "":
				os.remove(os.path.join(self.pssm))
			return False	

							
	def PSSM_Alert(self):
		if self.pssm != "":
			pssm_df = pd.read_csv(self.pssm,sep=",")
			sequence_numbers = np.unique(self.position) #collect sequence numbers of related chain ID
			if pssm_df.shape[0] == len(sequence_numbers):
				return True
			else:
				os.remove(os.path.join(self.pdb_file))
				os.remove(os.path.join(self.pssm))
				return False
		else:
			pass

	def Cut_off_Alert(self):
		chain_1_coord_float = []
		chain_2_coord_float = []
		with open("{}".format(self.pdb_file), "r") as pdbfile:
			for line in pdbfile:
				if line[:4] == "ATOM":
					self.chains.append(line[21])
					if line[21] == self.chn_1:
						splitted_chain_1 = [line[:6], line[6:11], line[12:16], line[17:20], line[21], line[22:26], line[30:38], line[38:46], line[46:54]]
						self.chain_1.append(splitted_chain_1)
						self.chain_1_coord.append(splitted_chain_1[6:9])
					elif line[21] == self.chn_2:
						splitted_chain_2 = [line[:6], line[6:11], line[12:16], line[17:20], line[21], line[22:26], line[30:38], line[38:46], line[46:54]]
						self.chain_2.append(splitted_chain_2)
						self.chain_2_coord.append(splitted_chain_2[6:9])
					

		for i in np.arange(0,len(self.chain_1),1):
			chain_1_coord_float.append([float(ele) for ele in self.chain_1_coord[i]])
		for i in np.arange(0,len(self.chain_2),1):
			chain_2_coord_float.append([float(ele) for ele in self.chain_2_coord[i]])

		aa_residues = []
		for i in np.arange(0,len(self.chain_1),1):
			for j in np.arange(0,len(self.chain_2),1):
				distance = ((chain_2_coord_float[j][0]-chain_1_coord_float[i][0])**2+(chain_2_coord_float[j][1]-chain_1_coord_float[i][1])**2+(chain_2_coord_float[j][2]-chain_1_coord_float[i][2])**2)**0.5
				if distance <= float(self.cut_off):
					aa_residues.append(distance)
					break
		
		if len(aa_residues) == 0:
			os.remove(self.pdb_file)
			return False
	
	def nameAlert(self):
		if "." in self.pdb:
			return False
		else:
			True
		
