import argparse

from gateway.core import EasyGateway

def main():
    parser = argparse.ArgumentParser(description="...")

    parser.add_argument("-c", "--config", type=str, help="Path to your config-file", default="config.yaml")
    
    args = parser.parse_args()


    # print(f"Path for your config -> {args.config}!")
    return args.config
    
if __name__ == "__main__":
    c_path = main()
    gateway = EasyGateway(config_path=c_path)
    print(f"Middleware count: {len(gateway.middlewares)}")
    gateway.run()