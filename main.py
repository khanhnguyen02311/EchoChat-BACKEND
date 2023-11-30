# "python main.py" to run the application
import uvicorn
from arguments import args
from components import serve_api, serve_grpc
from configurations import conf

api_server = serve_api(debug=args.debug, stage=args.stage)
grpc_server = serve_grpc(debug=args.debug, stage=args.stage)


@api_server.on_event('shutdown')
def shutdown():
    grpc_server.stop(2)
    print("INFO:\tGRPC Server stopped")


if __name__ == "__main__":
    grpc_server.add_insecure_port(f"[::]:{conf.Env.APP_PORT_GRPC}")
    grpc_server.start()
    print(f"INFO:\tGRPC Server started at port {conf.Env.APP_PORT_GRPC}")
    uvicorn.run(api_server, host="0.0.0.0", port=conf.Env.APP_PORT_API)
