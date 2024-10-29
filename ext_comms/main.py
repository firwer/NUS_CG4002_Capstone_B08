# main.py
import asyncio
import os
import sys
import argparse

from logger_config import setup_logger
from GameEngine import GameEngine

# Append parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize logger
logger = setup_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Run the game engine with the specified evaluation server port.")
    parser.add_argument('eval_server_port', type=int, help="The port on which the evaluation server is running.")
    return parser.parse_args()

async def main(eval_server_port):
    logger.info(f"Eval Server is running on port {eval_server_port}")
    ge = GameEngine(int(eval_server_port))
    logger.info("Starting Game Engine")
    await ge.start_game()

if __name__ == "__main__":
    args = parse_args()
    if sys.platform.lower() in ["win32", "nt"]:
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        logger.debug("Set Windows Selector Event Loop Policy")
    try:
        asyncio.run(main(args.eval_server_port))
    except Exception as e:
        logger.exception("An unexpected error occurred while running the main function.")