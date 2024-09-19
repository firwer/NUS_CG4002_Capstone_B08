import asyncio
import os
import sys
import argparse

from GameEngine import GameEngine


def parse_args():
    parser = argparse.ArgumentParser(description="Run the game engine with the specified evaluation server port.")
    parser.add_argument('eval_server_port', type=int, help="The port on which the evaluation server is running.")
    return parser.parse_args()


async def main(eval_server_port):
    print(f"Eval Server on port {eval_server_port}")
    ge = GameEngine(int(eval_server_port))
    print("Starting Game Engine")
    await ge.start_game()

if __name__ == "__main__":
    args = parse_args()
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args.eval_server_port))
