# Microsoft Fabric Accelerator
Welcome to the fabric-accelerator repository!

This accelerator helps you build a complete modern data platform with Microsoft Fabric. Whether you’re a data engineer, contributor, or simply exploring, this README provides everything you need to get started. 

Check out the video for an [overview](https://youtu.be/xuCPuezUm7E) of Fabric Accelerator.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
- [Collaborate](#collaborate)
- [Contact](#contact)

## Features
- Medallion architecture for both batch and real-time workloads <sup>[1](https://github.com/bennyaustin/fabric-accelerator/wiki/02-Architecture)</sup>.
- Metadata-driven orchestration using [ELT Framework](https://github.com/bennyaustin/elt-framework) <sup>[2](https://github.com/bennyaustin/fabric-accelerator/wiki/03-Metadata%E2%80%90driven-Orchestration)</sup> 
- Reusable Data Factory Pipelines that can be readily deployed with configuration changes <sup>[3](https://github.com/bennyaustin/fabric-accelerator/wiki/04-Data-Factory-Pipelines)</sup>
- Reusable Spark notebooks for common transformations <sup>[4](https://github.com/bennyaustin/fabric-accelerator/wiki/05-Spark-Notebooks)</sup>
- Reusable Real-Time Intelligence (RTI) items <sup>[5](https://github.com/bennyaustin/fabric-accelerator/wiki/11-Real%E2%80%90Time-Intelligence)</sup>
- Automated monitoring and optimization of Lakehouses <sup>[6](https://github.com/bennyaustin/fabric-accelerator/wiki/06-Lakehouse-Optimizations)</sup>
- Real-time Observability <sup>[7](https://github.com/bennyaustin/fabric-accelerator/wiki/10-Monitoring-and-Alerts-using-Fabric-Events)</sup>
- Real-time Insights into batch jobs <sup>[8](https://github.com/bennyaustin/fabric-accelerator/wiki/08-ELT-Insights)</sup>
- Automated Deployment <sup>[9](https://github.com/bennyaustin/fabric-accelerator/wiki/01-Set%E2%80%90up-Fabric-Accelerator)</sup>
- Reference [documentation](https://github.com/bennyaustin/fabric-accelerator/wiki) to assist your implementation.

## Getting Started
To get started follow these steps:
- Fork the repository: https://github.com/bennyaustin/fabric-accelerator.git
- Follow the instructions in the [set-up guide](https://github.com/bennyaustin/fabric-accelerator/wiki/01-Set%E2%80%90up-Fabric-Accelerator).


## Collaborate
You can collaborate in various ways, including:
- Pull Requests
- Update/Enrich [Wiki documentation](https://github.com/bennyaustin/fabric-accelerator/wiki)
- Raise [issues](https://github.com/bennyaustin/fabric-accelerator/issues) when you spot one
- Answer questions in the [discussion](https://github.com/bennyaustin/fabric-accelerator/discussions) forum

Please contact me to be added as a contributor.

## Contact
If you have any questions or need support, please contact the maintainer:
- [Benny Austin](https://github.com/bennyaustin)

# Deployment
This repo has GitHub Actions defined to support deployment - see [deploy-fabric-accelerator.yaml](./.github/workflows/deploy-fabric-accelerator.yml). It relies on hard-coded GUID references for "OLD" ids that are replaced with new IDs following deployment to a new workspace. Currently, each OLD ID must have existing references or the deployment will fail. This is to ensure that a bad ID isn't overlooked.

The deployment process utilizes the [Fabric CLI](https://microsoft.github.io/fabric-cli/). If you want to troubleshoot Fabric CLI commands locally, you can [install the Fabric CLI](https://microsoft.github.io/fabric-cli/#install) within your local VS Code environment. This assumes you already have the Python extension for VS Code installed. You may also want Git Bash installed since the actions use bash syntax. The recommended steps are:
* In VS Code, [create a new python environment](https://code.visualstudio.com/docs/python/environments#_creating-environments):
    * Hit F1, seach for Python: Create Environment. (Can choose default Venv option)
    * Select python interpreter
* Open a new Terminal window, you may choose to use a bash or PowerShell terminal
    * This should attempt to activate the environment automatically.
    * If this fails, you may need to [Set-ExecutionPolicy](https://code.visualstudio.com/docs/python/environments#_creating-environments:~:text=Tip%3A%20If%20the,RemoteSigned%20%2DScope%20Process)
* pip install ms-fabric-cli
* type "fab --version" to verify successful installation
