import yaml
import os
import zipfile
import tempfile
import re
from collections import defaultdict

def load_config():
    """Load configuration from config.yaml."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: config.yaml not found at {config_path}. Using empty config.")
        return {'packages_to_ignore': []}

def extract_zip(zip_path):
    """Extract zip file to a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

def should_include_line(line, ignored_packages):
    """Check if stack trace line should be included based on package."""
    if not line.strip().startswith('at '):
        return False

    # Extract the package/class path from the line
    # Format is typically: "at package.class.method(file:line)"
    package_path = line.strip()[3:].split('(')[0].strip()

    for package in ignored_packages:
        if package_path.startswith(package):
            return False
    return True

def parse_thread_dump(file_path, thread_pool_name, config=None):
    """Parse a thread dump file and extract relevant thread information."""
    # Get ignored packages from config
    ignored_packages = config.get('packages_to_ignore', []) if config else []

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Split content into individual thread sections
    thread_sections = content.split('"')

    threads = []

    for section in thread_sections:
        if thread_pool_name in section:
            lines = section.split('\n')
            for line in lines:
                if 'java.lang.Thread.State:' in line:
                    state = line.split(':')[1].strip()
                    stack_trace = []

                    # Collect and filter stack trace lines
                    for stack_line in lines[lines.index(line)+1:]:
                        if stack_line.strip().startswith('at '):
                            if should_include_line(stack_line, ignored_packages):
                                stack_trace.append(stack_line.strip())
                        elif not stack_line.strip():
                            break

                    if stack_trace:  # Only include if we have relevant stack trace lines
                        threads.append({
                            'state': state,
                            'stack_trace': tuple(stack_trace)  # Make it hashable
                        })
                    break

    return threads

def analyze_thread_dumps(temp_dir, thread_pool_name):
    """Analyze all thread dumps in the directory."""
    config = load_config()
    all_threads = []

    # Track thread states per file
    per_file_stats = []

    for file_name in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file_name)
        if os.path.isfile(file_path):
            threads = parse_thread_dump(file_path, thread_pool_name, config)
            all_threads.extend(threads)

            # Count states for threads in this file
            file_state_count = defaultdict(int)
            for thread in threads:
                file_state_count[thread['state']] += 1

            per_file_stats.append({
                'file_name': file_name,
                'state_count': dict(file_state_count),
                'total_threads': len(threads)
            })

    # Calculate averages per state
    state_sums = defaultdict(int)
    total_files = len(per_file_stats) if per_file_stats else 1  # Avoid division by zero
    all_states = set()

    for file_stat in per_file_stats:
        for state, count in file_stat['state_count'].items():
            state_sums[state] += count
            all_states.add(state)

    state_averages = {state: state_sums[state] / total_files for state in all_states}

    # Analyze stack traces
    stack_trace_count = defaultdict(int)
    stack_states = defaultdict(lambda: defaultdict(int))

    for thread in all_threads:
        if thread['stack_trace']:
            stack_trace_count[thread['stack_trace']] += 1
            stack_states[thread['stack_trace']][thread['state']] += 1

    # Sort stack traces by frequency
    sorted_stacks = sorted(stack_trace_count.items(), key=lambda x: x[1], reverse=True)

    results = {
        'stack_traces': sorted_stacks,
        'per_file_stats': per_file_stats,
        'stack_states': dict(stack_states),
        'state_averages': state_averages,
        'files_analyzed': total_files
    }

    return results
