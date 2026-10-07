# MARJADA

**Model-based Adaptive Reconstruction for Just-In-Time Activation and Deactivation**

> **WORK IN PROGRESS**

MARJADA is a model-based tool for verifying the implementability and realisability of runtime configurations in dynamically adaptable systems.

The tool verifies whether the current dynamic configuration remains realisable after a runtime adaptation. Whenever a feature is activated or deactivated, MARJADA reconstructs the resulting configuration and verifies whether the adapted configuration satisfies the required realisability conditions.

## Overview

Runtime adaptation can change the configuration of a system by activating or deactivating features. However, an adaptation may introduce inconsistencies with the dependencies and relations among the features.

MARJADA addresses this problem by verifying the resulting configuration after each runtime adaptation.


## Main Features

MARJADA currently supports:

* Runtime activation of features.
* Runtime deactivation of features.
* Reconstruction of the configuration after an adaptation.
* Verification of feature Runtime adaptation.
* Verification of Realisability of the valid configuration.


## Runtime Adaptation

For an activation request, MARJADA reconstructs the configuration required by the requested feature and checks whether the resulting configuration is realisable.

For a deactivation request, MARJADA determines which dependent features are affected and verifies whether the resulting configuration remains realisable after the requested feature is removed.

An adaptation is applied only when the resulting configuration satisfies the required conditions.

## Installation

MARJADA requires **Python 3**.

Install Python 3 on your system and verify the installation:

```bash
python3 --version
```

Then clone this repository:

```bash
git clone <repository-url>
cd MARJADA
```

## Running MARJADA

Run the main program using:

```bash
python3 main.py
```

The MARJADA interface will then start and allow runtime configuration adaptations to be analysed and verified.

## Project Status

This project is currently **work in progress**.

The implementation and documentation are still being developed, and additional features, verification capabilities, and case studies will be added in future versions.

## Research

MARJADA is developed as part of research on:

* Feature-model-based configuration.
* Runtime adaptation.
* Formal verification.
* Distributed and microservice-based systems.
* Configuration realisability.


## License

License information will be added in a future version.
