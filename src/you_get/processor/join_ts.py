#!/usr/bin/env python

"""
join_ts.py

A script to concatenate multiple .ts files into a single .ts file.

Usage: python join_ts.py --output TARGET.ts ts...

Options:
  -h, --help  show this help message and exit
  -o OUTPUT   specify the output file
"""

##################################################
# main
##################################################

from typing import List, Optional

def guess_output(inputs: List[str]) -> str:
    """
    Guesses the common prefix of the input file paths (excluding directories) and
    returns the base filename with a '.ts' extension. If no common prefix is found,
    returns 'output.ts'.

    Args:
        inputs (List[str]): A list of input file paths.

    Returns:
        str: The output file path.
    """
    import os.path

    # Extract the base name (filename without path) from each input
    inputs = map(os.path.basename, inputs)

    # Find the length of the shortest filename to limit comparisons.
    min_length = min(map(len, inputs))

    # Iterate over the range from 1 to the length of the shortest filename, in reverse order.
    for i in reversed(range(1, min_length)):
        # Check if all filenames have the same prefix of length `i`.
        if len(set(s[:i] for s in inputs)) == 1:
            return inputs[0][:i] + '.ts'

    # If no common prefix is found, return 'output.ts'.
    return 'output.ts'


def concat_ts(ts_parts: List[str], output: Optional[str] = None) -> str:
    """
    Concatenates multiple .ts files into a single .ts file.

    Args:
        ts_parts (List[str]): A list of .ts file paths to be concatenated.
        output (Optional[str], optional): The output file path. Defaults to None.

    Returns:
        str: The output file path.
    """
    assert ts_parts, 'No .ts files provided. Please provide at least one .ts file.'
    import os.path

    # Check if `output` is None or a directory. If so, append the output filename to the directory path.
    if not output:
        output = guess_output(ts_parts)
    elif os.path.isdir(output):
        output = os.path.join(output, guess_output(ts_parts))

    print('Merging video parts...')

    ts_out_file = open(output, "wb")
    for ts_in in ts_parts:
        ts_in_file = open(ts_in, "rb")
        ts_in_data = ts_in_file.read()
        ts_in_file.close()
        ts_out_file.write(ts_in_data)
    ts_out_file.close()
    return output


def usage() -> None:
    """
    Prints the usage information for the script.
    """
    print('Usage: [python3] join_ts.py --output TARGET.ts ts...')


def main() -> None:
    """
    Main function for the join_ts.py script.
    """
    import sys, getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:", ["help", "output="])
    except getopt.GetoptError as err:
        usage()
        sys.exit(1)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        else:
            usage()
            sys.exit(1)
    if not args:
        usage()
        sys.exit(1)

    concat_ts(args, output)

if __name__ == '__main__':
    main()
