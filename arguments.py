import argparse
from dotenv import load_dotenv

parser = argparse.ArgumentParser()
parser.add_argument("--stage", help="specify the development stage (dev/staging/prod)", type=str)
parser.add_argument("--debug", help="application debug mode (True/False), default: True", type=bool, default=True)
args = parser.parse_args()

if args.stage not in ["dev", "staging", "prod"]:
    parser.error("--stage: Invalid argument value (dev/staging/prod).")

load_dotenv(dotenv_path=f'.env.{args.stage}', verbose=True)
