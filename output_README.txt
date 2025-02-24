Interface amino acid list: Interfacial amino acid list (within a defined cut-off), belonging to the input chain ID, calculated by interface_residues.py. The same script outputs the pairwise contacts, as a Pairwise distance list.

Mutation models: Generated mutant models modeled by BuildMutant command of EvoEF1 or BuildModel command of FoldX.

Individual EvoEF1/FoldX files: EvoEF1/FoldX binding affinity predictions calculated by ComputeBinding of EvoEF1 or AnalyseComplex of FoldX (proton_scores).

Boxplot of EvoEF1/FoldX scores: All EvoEF1/FoldX binding affinity predictions are analyzed with the box-whisker statistics, where;

Depleting mutations: are defined by the positive outliers, and;

Enriching mutations: are defined by the negative outliers.

Heatmap of PROT-ON scores: All possible mutation energies are plotted as a heatmap for visual inspection.

Filtered mutations: Stability-filtered (uses ComputeStability command of EvoEF1 or Stability command of FoldX, where DDG-stability<0) enriching and depleting mutations and optionally PSSM-filtered (Enriching mutations with PSSM-score >0 && Depleting mutations with PSSM-score <=0).

Heatmap_df: A dataframe which is used to generate the heatmap.

Parameters: Parameters file including the submitted cut-off and IQR ranges.