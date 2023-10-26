# "python main.py" to run the application
import uvicorn
from arguments import args
from components import create_app
from configurations import conf

app = create_app(args.debug)

if __name__ == "__main__":
    uvicorn.run(app, port=conf.Env.APP_PORT)
