# EM-H01-human-single-neuron: LLM-Based Curation for Single-Cell Morphologies from the electron microscopic dataset H01

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19853169.svg)](https://doi.org/10.5281/zenodo.19853169)
[![Paper](https://img.shields.io/badge/Paper-10.64898%2F2025.12.26.696632-blue)](https://doi.org/10.64898/2025.12.26.696632)

## Overview
This repository contains the official codebase for the automated curation and evaluation of the human cortical neuron electron microscopy (EM) dataset (H01). It introduces an LLM-based system designed to advance single-cell neuroinformatics by utilizing structural priors to automatically generate, execute, and evaluate morphological curation scripts.

This work is associated with the publication:
> **Multimodal Data Fusion Reveals Morpho-Genetic Variations in Human Cortical Neurons Associated with Tumor Infiltration.**
> Yufeng Liu et al., 2025. [DOI: 10.64898/2025.12.26.696632](https://doi.org/10.64898/2025.12.26.696632)

## Repository Structure
The codebase is primarily organized into two functional pipelines:

* **`llmauto1/` (Prior-Enhanced Script Factory):** The core LLM-based generation system. This module utilizes established topological priors to programmatically generate custom curation and pruning scripts tailored to specific neuronal morphological anomalies. It was a compelling system in the ChatGPT-4/4o era, but feels somewhat dated in the age of ChatGPT-5.5 and OpenClaw.
* **Execution & Evaluation Scripts:** The remainder of the repository contains the necessary infrastructure to execute the auto-generated scripts from `llmauto1` against the raw `.swc` files. It also includes quantitative evaluation pipelines to assess the accuracy, topological validity, and overall quality of the refined reconstructions.

## Data Access
The corresponding curated morphological dataset, containing the reconstructed human cortical neurons derived from the H01 volume, is hosted publicly on Zenodo. 

* **Dataset Download:** [10.5281/zenodo.19853169](https://doi.org/10.5281/zenodo.19853169)

## Getting Started
*(Note: Please refer to the inline comments within individual scripts for specific argument requirements and environment setups).*

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/SEU-ALLEN-codebase/EM-H01-human-single-neuron.git](https://github.com/SEU-ALLEN-codebase/EM-H01-human-single-neuron.git)
    cd EM-H01-human-single-neuron
    ```

2.  **Generate Curation Scripts:** Navigate to the `llmauto1` directory to configure and run the LLM script factory based on your specific structural priors.

3.  **Execute and Evaluate:** Run the generated scripts on your local directory of `.swc` files, then utilize the root evaluation scripts to validate the pruning and branch-merging steps.

## Contributors
This project is mainly developed by Xiaoqin Gu before her graduation from Southeast University in 2025.

## Citation
If you utilize this codebase or the associated H01 curated dataset in your research, please cite our paper:

```bibtex
@article{liu2025multimodal,
  title={Multimodal Data Fusion Reveals Morpho-Genetic Variations in Human Cortical Neurons Associated with Tumor Infiltration},
  author={Liu, Yufeng and others},
  year={2025},
  doi={10.64898/2025.12.26.696632}
}
