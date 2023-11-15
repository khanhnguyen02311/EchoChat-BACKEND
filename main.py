# "python main.py" to run the application
import uvicorn
from arguments import args
from components import create_app
from configurations import conf

app = create_app(debug=args.debug, stage=args.stage)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=conf.Env.APP_PORT)
