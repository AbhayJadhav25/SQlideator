import cmd
from colorama import Fore, init

# initialize colorama for colored output
init(autoreset=True)

class SqlIdeatorCLI(cmd.Cmd):
    intro = Fore.CYAN + "SQL Ideator CLI (Validation Mode)\nType :q to exit\n"
    prompt = Fore.YELLOW + "sqlideator> "

    def __init__(self):
        super().__init__()
        self.buffer = []   # used for multi-line SQL input

    # This method handles all non-command input (SQL lines)
    def default(self, line):
        # exit command
        if line.strip() == ":q":
            print(Fore.RED + "Exiting SQL Ideator")
            return True

        # store each line in buffer
        self.buffer.append(line)

        # check if query ends with semicolon
        if line.strip().endswith(";"):
            query = "\n".join(self.buffer)
            self.buffer.clear()
            self.process_query(query)
            self.prompt = Fore.YELLOW + "sqlideator> "
        else:
            self.prompt = Fore.YELLOW + ".....> "

    # File-based validation command
    def do_validate(self, arg):
        """
        Validate SQL from file
        Usage: validate filename.sql
        """
        filename = arg.strip()

        if not filename:
            print(Fore.RED + "Filename required")
            return

        try:
            with open(filename, "r") as f:
                query = f.read()
        except FileNotFoundError:
            print(Fore.RED + "File not found")
            return

        print(Fore.BLUE + "\nFile loaded successfully")
        self.process_query(query)

    # Core processing (dummy validation for now)
    def process_query(self, query):
        print(Fore.BLUE + "\nValidating SQL...\n")

        # temporary validation logic (for CLI testing)
        if not query.strip().endswith(";"):
            print(Fore.RED + "✖ INVALID QUERY")
            print(Fore.RED + "Reason: Missing semicolon")
            return

        print(Fore.GREEN + "✔ QUERY RECEIVED SUCCESSFULLY")
