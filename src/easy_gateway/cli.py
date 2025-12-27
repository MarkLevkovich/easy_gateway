import argparse

from art import *

from easy_gateway.gateway.core import EasyGateway


def main():
    parser = argparse.ArgumentParser(
        description="🚀 Easy Gateway - simple API gateway",
        usage="easy-gateway [OPTIONS]",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to your config-file",
        default="config.yaml",
    )

    args = parser.parse_args()

    tprint("Easy Gateway", font="dancingfont")

    print("🚀 Start Easy Gateway...")
    print("─" * 60)
    print("─" * 15 + "SETTINGS" + "─" * 15)

    gateway = EasyGateway(config_path=args.config)

    gateway.run()


if __name__ == "__main__":
    main()
