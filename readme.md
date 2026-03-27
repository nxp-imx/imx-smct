# System Manager Config Tool Command Line Interface (SMCT CLI)

The System Manager Config Tool Command Line Interface is a Python-based configuration tool designed for NXP's System Manager firmware. SMCT serves as a bridge between human-readable configuration files and the low-level header files required for embedded system compilation.

## Table of contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick start guide](#quick-start-guide)
- [SMCT command line options](#smct-command-line-options)
- [JSON configuration files](#json-configuration-files)
- [SM project file structure](#sm-project-file-structure)
- [Common use cases](#common-use-cases)
- [Workflow examples](#workflow-examples)
- [Compiling SM using SMCT CLI instead of configtool.pl](#compiling-sm-using-smct-cli-instead-of-configtoolpl)
- [Common errors and solutions](#common-errors-and-solutions)

## Overview

SMCT provides a complete workflow for managing System Manager configurations:

- **Configuration Parsing**: Converts legacy CFG files into a structured JSON format for easier manipulation and version control
- **Resource Management**: Maintains a comprehensive database of hardware resources, constraints, and capabilities
- **Validation**: Ensures configuration consistency and catches conflicts before compilation
- **Code Generation**: Produces C header source code files for integration with firmware builds
- **Legacy Support**: Maintains compatibility with existing perl-based toolchains

## Prerequisites

- Operating Systems: Windows, Linux, macOS
- **Python 3.10** or higher
- Create and activate a virtual environment (venv, pipenv) to avoid conflicts with other packages (recommended)
- Upgrade pip to the latest version
- Get the System Manager Firmware (SM FW) project, it can be downloaded from https://github.com/nxp-imx/imx-sm
- Place the SMCT CLI tool either within the SM FW project root directory or at the same hierarchical level (recommended)
  - Default SM FW root directory path is `../` (can be overridden with `--sm_dir`)

## Installation

### GitHub - From sources
To install SMCT from the GitHub repository sources:
```bash
git clone https://github.com/nxp-imx/imx-smct.git
```

```bash
cd imx-smct
```

### Virtual environment setup
Create and activate the virtual environment and install the dependencies using the TOML configuration:
```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
python -m pip install --upgrade pip
```

```bash
pip install -U -e .
```

Alternatively, install dependencies:
```bash
pip install -r requirements.txt
```

## Quick start guide
This section provides brief instructions for getting started with SMCT.


### 1. Verify setup
Ensure that SMCT is properly located in relation to your SM FW project:

```bash
smct.py --version
```
Show the help message with all available options:


```bash
smct.py --help
```

### 2. Basic configuration generation
Convert an existing CFG file to header files (the most common use case):

```bash
smct.py -c ../configs/mx95evk.cfg -o my_project -f
```

This generates C header files in `sm_fw_root/configs/my_project/` ready for firmware compilation.

### 3. Full workflow setup
For complete project setup with JSON intermediate files for future editing:

```bash
smct.py -c ../configs/mx95evk.cfg -o my_project --store_db my_project --store_conf my_project --store_log my_project -f
```

### 4. Enhanced CFG export
Validate the existing CFG configuration and generate an enhanced CFG file with complete configuration and detailed comments:

```bash
smct.py -c ../configs/mx95evk.cfg --store_cfg_file ../configs/mx95evk_complete.cfg --store_log my_project -f
```

This creates a comprehensive CFG file with all available parameters, descriptions, and validation results - It can be used for documentation and sharing configurations.

### 5. Verify output
Check the generated files:
- **Header files**: `sm_fw_root/configs/my_project/config_*.h`
- **JSON config**: `sm_fw_root/configs/my_project/smct_configs/user_configuration.json`
- **Enhanced CFG**: `sm_fw_root/configs/mx95evk_complete.cfg` (if using step 4)
- **Validation log**: `sm_fw_root/configs/my_project/smct_configs/error_log.json`

### 6. Next steps
- **Modify configuration**: Edit `user_configuration.json` and regenerate with `-i my_project -o my_project -f`
- **Validate changes**: Check `error_log.json` for any configuration issues
- **Share configurations**: Use enhanced CFG files for better team collaboration
- **Integration**: Include generated headers in your SM FW build

### 7. Integrating SMCT into SM Makefile build
The SM FW Makefile uses the **SMCT** environment variable to locate the SMCT CLI configuration tool during *make cfg* execution. Either pass a relative path to the SMCT tool when invoking *make*, or set the SMCT environment variable to an absolute path to the tool. The Makefile automatically verifies Python and the tool functionality and uses the SMCT if possible, otherwise it falls back to using the legacy configtool.pl.

Using Makefile, compile the SM firmware application with the specified configuration in CFG using the SMCT CLI:

```bash
make cfg config=mx95evk SMCT=../smct
```

Alternatively:
```bash
make all config=mx95evk SMCT=../smct
```

For more details, see the SM FW documentation.

### Quick reference table
| Task | Command Pattern | Example |
|------|----------------|---------|
| CFG → Headers | `-c CFG -o DIR -f` | `smct.py -c mx95evk.cfg -o my_proj -f` |
| CFG → JSON + Headers | `-c CFG -o DIR --store_* DIR -f` | `smct.py -c mx95evk.cfg -o proj --store_conf proj -f` |
| JSON → Headers | `-i DIR -o DIR -f` | `smct.py -i proj -o proj -f` |
| CFG → Extended CFG | `-c CFG --store_cfg_file DIR` | `smct.py -c mx95evk.cfg --store_cfg_file ../configs/mx95evk_ext.cfg` |
| Validate Only | `-c CFG --store_log DIR` | `smct.py -c mx95evk.cfg --store_log validation` |

## SMCT command line options
The following options can be used to run SMCT CLI

### Basic options
```
-v, --version               Show the version of the SMCT CLI tool.
                                        Parameters: None (flag only)
                            
-h, --help                  Show the help message with all available options and exit.
                                        Parameters: None (flag only)
```

### Dependencies directory configuration options
```
--sm_dir                    Overwrite the root directory of the System Manager FW repository/project, default: '[this_tool_path]/..'.
                                        Parameters: Absolute or relative path string
                                        Example: --sm_dir /path/to/sm_fw_root
                            
--soc_dir                   Overwrite the directory to SoC static resources (sm_model), default: '[this_tool_path]/sm_model'. This option is supported for the SM GUI tool.
                                        Parameters:  Path to SoC resources named sm_model
                                        Example: --soc_dir /path/to/soc_resources
```

### Input/output options
```
-c, --load_cfg              Load the System Manager user configuration from the board CFG file.
                                        Parameters: Absolute path to the .cfg file or the configuration file name to be found in the loaded SM FW project
                                        Example: -c ../configs/mx95evk.cfg or -c mx95evk.cfg
                            
-i, --input                 Load the System Manager user configuration from the JSON file by setting the input directory of the user_configuration.json file located in 'smct_configs'.
                                        Parameters: Absolute/relative path to the 'smct_configs' directory or a path relative to the 'sm_fw_root/configs/' path
                                        Example: -i project_name or -i /absolute/path/to/project_name
                            
-o, --output                Generate output by setting the output directory where configuration header files are stored (requires --force flag if directory exists).
                                        Parameters: Absolute/relative path to store the generated output or a path relative to the default 'sm_fw_root/configs/' path
                                        Example: -o project_name or -o /path/to/project_name
```

### Storage options
```
--store_db                  Store JSON database files 'atomic_resources.json', 'macro_resources.json' and 'chip_data.json' 
                                to the 'smct_configs' folder (requires --force flag if directory exists).
                                        Parameters: Absolute/relative path where the 'smct_configs' directory is created or a path relative to the 'sm_fw_root/configs/' path
                                        Example: --store_db project_name or --store_db /path/to/project_name
                            
--store_conf                Store user configuration 'user_configuration.json'
                                to the 'smct_configs' folder (requires --force flag if directory exists).
                                        Parameters: Absolute/relative path where the 'smct_configs' directory is created or a path relative to the 'sm_fw_root/configs/' path
                                        Example: --store_conf project_name or --store_conf /path/to/project_name
                            
--store_log                 Store problem reports log 'error_log.json'
                                to the 'smct_configs' folder (requires --force flag if directory exists).
                                        Parameters: Absolute/relative path where the 'smct_configs' directory is created or a path relative to the 'sm_fw_root/configs/' path
                                        Example: --store_log project_name or --store_log /path/to/project_name
                            
--store_cfg_file            Store the existing configuration in the original CFG file format. Specify a full path to the destination file with the .cfg extension. 
                                (requires --force flag if file exists)
                                        Parameters: Full file path where the new CFG is stored.
                                        Example: --store_cfg_file output/board_config.cfg
```

### Device/board selection (internal use - SM GUI tool)
```
-l, --load_device           Load SM FW files related to a specific device. This option requires additional options -d/--device and -b/--board to be specified.
                                The purpose is to parse device files in the SM GUI tool.   
                                        Parameters: None (flag only)
                            
-b, --board                 Enforce a specific board name (identifier) that exists in the 'sm_fw_root/boards' directory.
                                        Parameters: SM FW board identifier
                                        Example: -b mcimx95evk
                            
-d, --device                Enforce a specific device/SoC name (identifier) that exists in the 'sm_fw_root/devices' directory.
                                        Parameters: SM FW device (SoC) identifier
                                        Example: -d MIMX95
```

### Utility options
```
-f, --force                 Force overwriting of existing output files. It applies to all stored JSON files and generated source code output.
                                **Warning:** it overwrites all files without confirmation.
                                        Parameters: None (flag only)
```

### Path handling
Options that require a PATH parameter, such as `-i, --input`, `-o, --output` and storage options support:

- **Simple project names**: Resolved relative to the `configs` folder in the SM FW project root
- **Absolute paths**: Full filesystem paths for temporary or custom locations
- **Relative paths**: Relative to the current working directory

## JSON configuration files

The SMCT tool works with three main types of JSON files stored in the `smct_configs` subfolder:

### Resource database
- **Purpose**: Contains complete hardware resource definitions and capabilities
- **Files**: atomic_resources.json, macro_resources.json, chip_data.json
- **Content**:  
                            - Atomic resources: pins, clocks, power domains, ...  
                            - Macro resources - hardware peripheral definitions  
                            - SoC-specific resource constraints 
                            - Default configurations  
- **Generated from**: SM header files and SoC model definitions
- **Usage**: Serves as the foundation for configuration validation and generation

### User configuration
- **Purpose**: Contains user-specific board configuration choices
- **Files**: user_configuration.json
- **Content**:  
                            - User-selected board configuration parameters  
                            - Custom board-specific definitions
- **Generated from**: Board CFG files (for example, mx95evk.cfg)
- **Usage**: Defines the actual configuration to be applied to the target board

### Error log
- **Purpose**: Contains validation results, information, warnings, and error reports from configuration processing
- **Files**: error_log.json
- **Content**:  
                            - Configuration validation errors and warnings  
                            - Processing status and diagnostic information  
                            - Troubleshooting details for failed operations   
- **Generated from**: SMCT validation and processing operations
- **Usage**: Provides detailed feedback for debugging configuration issues and ensuring system reliability.


**Error log analysis**  
The `error_log.json` file contains structured error information:
- 🔴 `fatals`: Critical issues that prevent from processing (tool stops)
- 🟠 `errors`: Issues that cause compilation or build failures  
- 🟡 `warnings`: Non-critical issues that may affect functionality
- ℹ️ `info`: Processing status and diagnostic information

## SM project file structure
```
📁 imx-smct/                              ← SM Config Tool CLI root
│   ├── 📄 smct.py                        ← Main SMCT CLI tool
│   ├── 📄 readme.md                      ← SMCT documentation
│   ├── 📁 sm_model/                      ← SM and SOC resource files
│   └── 📁 smct/                          ← SMCT source code modules
│
📁 sm_fw_root/                            ← SM Firmware root 
├── 📁 configs/
│   └── 📁 my_project/                    ← Your project folder, generated files (for example, mx95evk)
│       ├── 📁 smct_configs/              ← JSON database and config
│       │   ├── 📄 user_configuration.json    ← Board configuration (edit this file)
│       │   ├── 📄 atomic_resources.json      ← Hardware low-level resources
│       │   ├── 📄 macro_resources.json       ← Peripheral definitions, subsystems  
│       │   ├── 📄 chip_data.json             ← SoC information
│       │   └── 📄 error_log.json             ← Validation results
│       └── 📄 config_*.h                 ← Generated headers
├── 📁 devices/                           ← Supported SM FW devices
│   └── 📁 [device_name]/                 ← SoC/device-specific definitions (for example, MIMX95)
│       ├── 📁 sm/                        ← Device header files
│       └── 📁 configtool/                ← Device CFG files
└── 📁 boards/                            ← Supported SM FW boards
    └── 📁 [board_name]/                  ← Board-specific definitions (for example, mcimx95evk)
        └── 📁 sm/                        ← Board header files
```

**Directory descriptions:**
- **configs/project_name/**: The user project workspace containing JSON database, configurations, and generated output files.
- **devices/**: Contains SoC/device-specific hardware definitions and capabilities for different chip families stored as SM FW header files and configuration tool CFG definitions.
- **boards/**: Contains board-specific hardware layout, pin assignments, and peripheral connections for different development boards stored as SM FW header files.

## Common use cases

### 1. New board setup or configuration refresh
Convert the CFG configuration file to a JSON format and generate the output configuration headers:

```bash
smct.py -c ../configs/mx95evk.cfg -o project_name --store_db project_name --store_conf project_name --store_log project_name -f
```

**What this does:**
- Loads the board configuration from the CFG file
- Generates configuration header files in the output directory
- Creates a JSON resource database for future use
- Creates a JSON user configuration for future modifications
- Creates a JSON problem report log
- Forces overwrite of existing files

**Note**: To refresh (update) database only, omit `--store_conf` option to run the command without overwriting of existing (modified) user configuration. Otherwise, the original configuration defined in *mx95evk.cfg* is used.

### 2. Generate headers from existing JSON configuration
Regenerate header files from previously created JSON files:

```bash
smct.py -i project_name -o project_name --store_log project_name
```

**What this does:**
- Reads JSON files from `project_name/smct_configs/`
- Generates fresh configuration header files
- Preserves the existing JSON configuration files
- Updates the validation log with processing results

### 3. Export JSON configuration to extended CFG format
Export the existing JSON configuration to a CFG format with additional comments and complete configuration, including the *device.cfg* default settings:

```bash
smct.py -i project_name --store_cfg_file output/enhanced_board_config.cfg --store_log project_name -f
```

**What this does:**
- Reads the existing JSON configuration files from `project_name/smct_configs/`
- Exports the configuration in a legacy CFG format with enhanced comments
- Includes a superset of all available configuration parameters
- Adds descriptive comments for better understanding
- Creates a validation log for export process
- Useful for documentation, sharing configurations, or creating configurations used in automation builds such as Yocto

### 4. Re-export original CFG to extended CFG format
Process and re-export the CFG file directly with enhanced formatting and comments:

```bash
smct.py -c ../configs/mx95evk.cfg --store_cfg_file output/enhanced_mx95evk.cfg --store_log project_name -f
```

**What this does:**
- Loads the original CFG file and processes it through SMCT
- Re-exports CFG with enhanced comments and formatting
- Includes superset of configuration parameters with descriptions
- Validates the original configuration and adds helpful annotations
- Creates a validation log with processing results and any issues found
- Creates an improved CFG file for better readability and documentation

### 5. Working with custom directories
Use absolute paths for temporary or non-standard locations:

```bash
smct.py -i C:\Temp\sm\my_project -o C:\Temp\sm\my_project_output
```

**Requirements:**
- The input directory must contain the `smct_configs` subfolder with valid JSON files
- The output directory is created if it does not exist

### 6. Legacy CFG-to-headers conversion
Direct conversion without JSON intermediate files (legacy mode):

```bash
smct.py -c ../configs/mx95evk.cfg -o mx95evk -f
```

**What this does:**
- Converts CFG directly into header files
- Skips creation of intermediate JSON files
- Ensures compatibility with the legacy perl script workflow
- Provides the fastest option for generating output configurations

## Workflow examples

### Verify setup
1. Ensure that SMCT is properly located in relation to to your SM FW project or use the `--sm_dir` option to set the valid SM FW project directory with every command
2. Run `smct.py --version` to verify installation and compatibility

### Initial board bring-up
1. Create a board CFG file or modify a similar existing board CFG file, for example from `../configs/` directory
2. Run: `smct.py -c board.cfg -o board_name --store_db board_name --store_conf board_name --store_log board_name -f`
3. Review generated headers (and, optionally, JSON files)
4. Optionally, modify the JSON user configuration as needed and regenerate: `smct.py -i board_name -o board_name --store_log board_name -f`

### Configuration iteration
1. Edit the JSON user configuration file manually
2. Regenerate headers: `smct.py -i project_name -o project_name --store_log project_name -f`
3. Test and repeat as needed

### Validation and re-export of existing CFG configuration
1. Import the existing configuration: `smct.py -c mx95evk.cfg --store_cfg_file mx95evk_extended.cfg --store_log mx95evk -f`
2. Review the validation log for any issues or warnings
3. Use a validated re-exported CFG file to review the complete configuration

### Continuous integration pipeline
1. Validate the configuration automatically: `smct.py -c ${BOARD_CONFIG} --store_log ci_validation_${BUILD_ID}`
2. Generate build headers: `smct.py -c ${BOARD_CONFIG} -o ${OUTPUT_DIR} -f`
3. Archive an extended configuration: `smct.py -c ${BOARD_CONFIG} --store_cfg_file artifacts/${BOARD_NAME}_${BUILD_ID}.cfg -f`  
*Note:* This flow can be executed in one single command.

## Compiling SM using SMCT CLI instead of configtool.pl
The SM application can be fully compiled using the Makefile. For more details, see the SM FW documentation.

1. Create a board CFG file, modify a similar existing board CFG file or export an extended CFG configuration
2. Run: `make cfg config=mx95evk SMCT=../smct` or `make all config=mx95evk SMCT=../smct`
   
Note: The *SMCT* variable can be configured in the mak file or passed as a command-line argument to specify the path to the SMCT tool. Make sure that it points to the correct relative or absolute path of the SMCT CLI tool. See the Quick start's guide [Section 7](#7-integrating-smct-into-sm-makefile-build) above for more details.

## Common errors and solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `SM FW root directory not found` | SMCT cannot find the SM firmware project | Use `--sm_dir /path/to/sm_fw` or ensure SMCT is in the correct location |
| `Permission denied` | Files already exist | Add `-f` flag to force overwrite |
| `Configuration validation failed` | Invalid CFG parameters | Check `error_log.json` for specific issues |
| `Python version not supported` | Python < 3.10 | Upgrade to Python 3.10+ |
