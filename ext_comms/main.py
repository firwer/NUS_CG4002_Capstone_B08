import asyncio
import os
import sys

from GameEngine import GameEngine


async def main():
    eval_server_port = ""
    while len(eval_server_port) == 0:
        eval_server_port = input("Please Provide Evaluation Server Port: ")

    ge = GameEngine(int(eval_server_port))
    print("Starting Game Engine")
    await ge.start_game()

if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(main())
