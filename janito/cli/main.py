# Ensure all output is written before the program exits, especially when output is piped or buffered.
import atexit, sys
atexit.register(lambda: sys.stdout.flush())
from janito.cli.main_cli import JanitoCLI

def main():
    cli = JanitoCLI()
    cli.run()

if __name__ == "__main__":
    main()
