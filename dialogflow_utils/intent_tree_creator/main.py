import sys
import os
sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

from intent_tree_creator import IntentTreeCreator

config = {}

creator = IntentTreeCreator(config)
creator.run()