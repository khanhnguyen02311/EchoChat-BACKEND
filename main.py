# "python main.py" to run the application

import uvicorn
from components import create_app
from configurations.conf import Env

app = create_app(Env.APP_DEBUG)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=Env.APP_PORT)
