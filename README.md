# ALC Tableau Implementation

This repository contains an implementation of the ALC Tableau algorithm for determining whether a given query in Negation Normal Form (NNF) is entailed by a Knowledge Base (KB).

## Overview

The ALC Tableau method is designed to determine the satisfiability of a given concept with respect to a knowledge base in the ALC Description Logic. The provided implementation checks if a given NNF query is entailed by the KB.

## Methodology

1. **Conversion**: Transform the NNF query into a concept in ALC Description Language and convert the KB into ALC TBox and ABox.
2. **Graph Initialization**: Initialize the completion graph from the ABox.
3. **Axiom Application**: Apply all TBox axioms to all individuals as well as unblocked variables.
4. **Backtracking**: In the event of a contradiction, backtrack and explore remaining t-branches.
5. **Termination**: The tableau terminates when all branches are either CLOSED or COMPLETE. If all branches are CLOSED, the NNF query is not entailed by the KB. If they are COMPLETE, then the NNF query is entailed by the KB.

## Assumptions

- Both the NNF query and KB are in ALC Description Language.
- Proper conversion of both has been carried out before applying them to the ALC Tableau.
- All TBox axioms are applied to individuals and unblocked variables before checking for contradictions.

## Results

The implemented ALC Tableau algorithm works correctly on given inputs, ensuring expected behavior for constructed input cases.

## Usage

1. Ensure you have the required Python dependencies installed.
2. Run the main Python script to process the sample knowledge base and query files:
\```bash
python CS19B012.py
\```
3. (Optional) You can replace the sample knowledge base and query files with your own and adapt the path in the main script.
