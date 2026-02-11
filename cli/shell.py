import cmd
from colorama import Fore, Style, init

# initialize colorama for colored output
init(autoreset=True)

class SqlIdeatorCLI(cmd.Cmd):
    intro = Fore.CYAN + r"""
   _____   ____   _      _      _        _           _             
  ░▒▓███████▓▒░░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░▒▓██████▓▒░░▒▓███████▓▒░  
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  
       ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
       ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓████████▓▒░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░ 
                ░▒▓█▓▒░                                                                                       
                 ░▒▓██▓▒░                                                                                        

                SQL Ideator - Validation CLI
                Type :q to exit
""" + Style.RESET_ALL

    prompt = Fore.YELLOW + "sqlideator> "

    def __init__(self):
        super().__init__()
        self.buffer = []

    def default(self, line):
        if line.strip() == ":q":
            print(Fore.RED + "Exiting SQL Ideator")
            return True

        self.buffer.append(line)

        if line.strip().endswith(";"):
            query = "\n".join(self.buffer)
            self.buffer.clear()
            self.process_query(query)
            self.prompt = Fore.YELLOW + "sqlideator> "
        else:
            self.prompt = Fore.YELLOW + ".....> "

    def do_validate(self, arg):
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

    def process_query(self, query):
        print(Fore.BLUE + "\nValidating SQL...\n")

        if not query.strip().endswith(";"):
            print(Fore.RED + "✖ INVALID QUERY")
            print(Fore.RED + "Reason: Missing semicolon")
            return

        print(Fore.GREEN + "✔ QUERY RECEIVED SUCCESSFULLY")
