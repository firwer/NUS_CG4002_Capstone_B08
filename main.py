from GameEngine import GameEngine


def main():
    eval_server_port = ""
    while len(eval_server_port) == 0:
        eval_server_port = input("Please Provide Evaluation Server Port: ")

    ge = GameEngine(int(eval_server_port))
    print("Starting Game Engine")
    ge.start_game()


if __name__ == "__main__":
    main()
