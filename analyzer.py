import os
import zipfile
import tempfile
import re
from collections import defaultdict

def extract_zip(zip_path):
    """Extract zip file to a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

def parse_thread_dump(file_path, thread_pool_name):
    """Parse a thread dump file and extract relevant thread information."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Split content into individual thread sections
    thread_sections = content.split('"')

    threads = []
    current_thread = None

    for section in thread_sections:
        if thread_pool_name in section:
            lines = section.split('\n')
            for line in lines:
                if 'java.lang.Thread.State:' in line:
                    state = line.split(':')[1].strip()
                    stack_trace = []
                    for stack_line in lines[lines.index(line)+1:]:
                        if stack_line.strip().startswith('at '):
                            stack_trace.append(stack_line.strip())
                        elif not stack_line.strip():
                            break

                    if stack_trace:
                        threads.append({
                            'state': state,
                            'stack_trace': tuple(stack_trace)  # Make it hashable
                        })

    return threads

def analyze_thread_dumps(temp_dir, thread_pool_name):
    """Analyze all thread dumps in the directory."""
    all_threads = []

    for file_name in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file_name)
        if os.path.isfile(file_path):
            threads = parse_thread_dump(file_path, thread_pool_name)
            all_threads.extend(threads)

    # Analyze stack traces
    stack_trace_count = defaultdict(int)
    state_count = defaultdict(int)
    stack_states = defaultdict(lambda: defaultdict(int))

    for thread in all_threads:
        if thread['stack_trace']:
            stack_trace_count[thread['stack_trace']] += 1
            state_count[thread['state']] += 1
            stack_states[thread['stack_trace']][thread['state']] += 1

    # Sort stack traces by frequency
    sorted_stacks = sorted(stack_trace_count.items(), key=lambda x: x[1], reverse=True)

    results = {
        'stack_traces': sorted_stacks,
        'state_count': dict(state_count),
        'stack_states': dict(stack_states)
    }

    return results
