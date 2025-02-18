# Java Thread Pool Analyzer

A command-line tool for analyzing Java thread dumps to identify thread pool saturation issues and common stack traces.

## Overview

This tool helps diagnose thread pool issues in Java applications by:
- Analyzing multiple thread dumps from a ZIP file
- Identifying thread states and their distribution
- Finding common stack traces that might indicate bottlenecks
- Highlighting potential causes of thread pool saturation
- Filtering out common framework/library stack traces for better focus on application code

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - `pyyaml`
  - `curses` (typically included in standard Python installation)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd thread-pool-analyzer
```

2. Install required packages:
```bash
pip install pyyaml
```

## Usage

### Basic Usage

Run the program with:
```bash
python thread_analyzer.py -z <path-to-zip-file> -tp <thread-pool-name>
```

Example:
```bash
python thread_analyzer.py -z thread_dumps.zip -tp "http-nio-8080-exec"
```

### Command Line Arguments

- `-z, --zip-file`: Path to the ZIP file containing thread dumps
- `-tp, --thread-pool-name`: Name of the thread pool to analyze

### Interactive Mode

If you run the program without arguments, it will prompt for the required information:
```bash
python thread_analyzer.py
```

### Help

To see all available options:
```bash
python thread_analyzer.py --help
```

[rest of the README remains the same...]
```

3. Make sure the imports in `analyzer.py` are still correct.

The directory structure should now look like:
```
thread-pool-analyzer/
├── analyzer.py
├── thread_analyzer.py
├── config.yaml
└── README.md
```

4. The command to run the help would now show:
```bash
$ python thread_analyzer.py --help
usage: thread_analyzer.py [-h] [-z ZIP_FILE] [-tp THREAD_POOL_NAME]

Analyze Java thread dumps for thread pool saturation.

optional arguments:
  -h, --help            show this help message and exit
  -z ZIP_FILE, --zip-file ZIP_FILE
                        Path to the ZIP file containing thread dumps
  -tp THREAD_POOL_NAME, --thread-pool-name THREAD_POOL_NAME
                        Name of the thread pool to analyze (e.g., "http-nio-8080-exec")

Examples:
    python thread_analyzer.py -z threads.zip -tp "http-nio-8080-exec"
    python thread_analyzer.py --zip-file dumps.zip --thread-pool-name "ForkJoinPool.commonPool"
```
