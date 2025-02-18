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

def display_results(stdscr, results):
    """Display analysis results using curses."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    stdscr.clear()
    current_line = 0
    max_y, max_x = stdscr.getmaxyx()

    def safe_addstr(y, x, string, *args):
        """Safely add a string to the screen, truncating if necessary."""
        try:
            if y < max_y:
                # Truncate the string to fit the screen width
                available_width = max_x - x
                if len(string) > available_width:
                    string = string[:available_width-3] + "..."
                stdscr.addstr(y, x, string, *args)
                return True
            return False
        except curses.error:
            return False

    # Display thread states summary
    if safe_addstr(current_line, 0, "Thread States Summary:", curses.A_BOLD):
        current_line += 1

    for state, count in results['state_count'].items():
        if not safe_addstr(current_line, 2, f"{state}: {count}"):
            break
        current_line += 1

    current_line += 1
    if safe_addstr(current_line, 0, "Stack Trace Analysis:", curses.A_BOLD):
        current_line += 2

    # Display top stack traces
    for stack_trace, count in results['stack_traces']:
        # Check if we're near the bottom of the screen
        if current_line >= max_y - 5:
            safe_addstr(max_y-2, 0, "Press any key to continue (q to quit)...")
            stdscr.refresh()
            ch = stdscr.getch()
            if ch == ord('q'):
                break
            current_line = 0
            stdscr.clear()

        # Display count
        if safe_addstr(current_line, 0, f"Count: {count}", curses.color_pair(1)):
            current_line += 1

        # Display states for this stack trace
        states = results['stack_states'][stack_trace]
        state_str = ", ".join(f"{state}: {cnt}" for state, cnt in states.items())
        if safe_addstr(current_line, 0, f"States: {state_str}", curses.color_pair(2)):
            current_line += 1

        # Display stack trace
        for line in stack_trace:
            if not safe_addstr(current_line, 2, line):
                break
            current_line += 1

        current_line += 1

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
