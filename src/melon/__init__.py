import sys

from dublib.functions.system import check_python_minimal_version

from .cli.orchestrator import CommandsOrchestrator
from .core.system_objects import SystemObjects

def main():
	check_python_minimal_version(3, 12)

	objects: SystemObjects = SystemObjects()
	called_commands: str = sys.argv[0].split("/")[-1]

	CommandsOrchestrator(objects).run(called_commands)

if __name__ == "__main__":
	main()
