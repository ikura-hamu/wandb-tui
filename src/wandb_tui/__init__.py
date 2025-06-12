from .app import WandbTUI


def main() -> None:
    app = WandbTUI()
    app.run()


if __name__ == "__main__":
    main()
