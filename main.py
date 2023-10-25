# "python main.py" to run the application
import uvicorn
from os import environ
from arguments import args
from components import create_app

app = create_app(args.debug)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(environ.get("APP_PORT")))
