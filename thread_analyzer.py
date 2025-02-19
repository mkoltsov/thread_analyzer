#!/usr/bin/env python3
import curses
import sys
import argparse
from analyzer import extract_zip, analyze_thread_dumps

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze Java thread dumps for thread pool saturation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    python ui.py -z threads.zip -tp "http-nio-8080-exec"
    python ui.py --zip-file dumps.zip --thread-pool-name "ForkJoinPool.commonPool"
        '''
    )

    parser.add_argument(
        '-z', '--zip-file',
        type=str,
        help='Path to the ZIP file containing thread dumps'
    )

    parser.add_argument(
        '-tp', '--thread-pool-name',
        type=str,
        help='Name of the thread pool to analyze (e.g., "http-nio-8080-exec")'
    )

    args = parser.parse_args()

    # If arguments are not provided, prompt for them
    if not args.zip_file:
        args.zip_file = input("Enter path to zip file: ")
    if not args.thread_pool_name:
        args.thread_pool_name = input("Enter thread pool name to analyze: ")

    return args

def format_stack_trace(stack_trace):
    """Format stack trace for better readability."""
    formatted = []
    for line in stack_trace:
        # Remove any unwanted line breaks or carriage returns
        line = line.strip()
        if line.startswith('at '):
            # Ensure the full line is preserved
            formatted.append(line)
    return formatted

def display_results(stdscr, results):
    """Display analysis results using curses."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

    stdscr.clear()
    current_line = 0
    max_y, max_x = stdscr.getmaxyx()

    def safe_addstr(y, x, string, *args):
        """Safely add a string to the screen, truncating if necessary."""
        try:
            if y < max_y:
                available_width = max_x - x
                if len(string) > available_width:
                    string = string[:available_width-3] + "..."
                stdscr.addstr(y, x, string, *args)
                return True
            return False
        except curses.error:
            return False

    # Display thread states summary
    if safe_addstr(current_line, 0, "Thread Pool States Summary:", curses.A_BOLD):
        current_line += 1

    if safe_addstr(current_line, 2, f"Files analyzed: {results['files_analyzed']}"):
        current_line += 2

    if not results.get('state_averages'):
        safe_addstr(current_line, 0, "No matching threads found in the analyzed files.", curses.color_pair(3))
        current_line += 3
    else:
        # Display average states
        if safe_addstr(current_line, 0, "Average thread count per state:", curses.A_BOLD):
            current_line += 1

        for state, avg in sorted(results['state_averages'].items()):
            if not safe_addstr(current_line, 2, f"{state}: {avg:.1f} threads"):
                break
            current_line += 1

        # Display per-file details
        current_line += 1
        if safe_addstr(current_line, 0, "Per-file details:", curses.A_BOLD):
            current_line += 1

        for file_stat in results['per_file_stats']:
            if safe_addstr(current_line, 0, f"\nFile: {file_stat['file_name']}", curses.color_pair(2)):
                current_line += 1

            if safe_addstr(current_line, 2, f"Total threads in pool: {file_stat['total_threads']}"):
                current_line += 1

            # Display state distribution for this file
            for state, count in file_stat['state_count'].items():
                percentage = (count / file_stat['total_threads'] * 100) if file_stat['total_threads'] > 0 else 0
                if not safe_addstr(current_line, 2, f"{state}: {count} ({percentage:.1f}%)"):
                    break
                current_line += 1

    # Add separator before stack traces
    current_line += 1
    if safe_addstr(current_line, 0, "=" * (max_x - 1), curses.A_DIM):
        current_line += 1

    if safe_addstr(current_line, 0, "Stack Trace Analysis:", curses.A_BOLD):
        current_line += 2

    # Get the highest count for comparison
    max_count = max((count for stack_trace, count in results.get('stack_traces', [])), default=0)

    # Display top stack traces
    for stack_trace, count in results.get('stack_traces', []):
        # Check if we're near the bottom of the screen
        if current_line >= max_y - 5:
            safe_addstr(max_y-2, 0, "Press any key to continue (q to quit)...")
            stdscr.refresh()
            ch = stdscr.getch()
            if ch == ord('q'):
                break
            current_line = 0
            stdscr.clear()

        # Display count with different emphasis based on whether it's the highest
        count_color = curses.color_pair(5) | curses.A_BOLD if count == max_count else curses.color_pair(1)
        if count == max_count:
            if safe_addstr(current_line, 0, f"Count: {count} (HIGHEST)", count_color):
                current_line += 1
        else:
            if safe_addstr(current_line, 0, f"Count: {count}", count_color):
                current_line += 1

        # Display states for this stack trace
        states = results['stack_states'][stack_trace]
        state_str = ", ".join(f"{state}: {cnt}" for state, cnt in states.items())
        if safe_addstr(current_line, 0, f"States: {state_str}", curses.color_pair(2)):
            current_line += 1

        # Display stack trace with indicator on first line if count > 1
        for i, line in enumerate(stack_trace):
            if i == 0:  # First line of the stack trace
                if count > 1:  # Only add indicator if count > 1
                    indicator = " <-------- 🪲 Most likely is causing TP saturation"
                    if count == max_count:
                        indicator += " (HIGHEST OCCURRENCE)"
                    line_with_indicator = line + indicator
                    highlight_color = curses.color_pair(5) | curses.A_BOLD if count == max_count else curses.color_pair(4)
                    if not safe_addstr(current_line, 2, line_with_indicator, highlight_color):
                        safe_addstr(current_line, 2, line)  # Fallback if no space for indicator
                else:
                    safe_addstr(current_line, 2, line)
            else:
                if not safe_addstr(current_line, 2, line):
                    break
            current_line += 1

        current_line += 1  # Add extra space between stack traces

    # Final pause
    safe_addstr(max_y-1, 0, "Press any key to exit...")
    stdscr.refresh()
    stdscr.getch()

def main():
    # Parse command line arguments
    args = parse_arguments()

    # Extract and analyze
    temp_dir = extract_zip(args.zip_file)
    results = analyze_thread_dumps(temp_dir, args.thread_pool_name)

    # Display results using curses
    curses.wrapper(lambda stdscr: display_results(stdscr, results))

if __name__ == "__main__":
    main()
