# "python main.py --stage dev" to run the application
import asyncio
import uvicorn
from arguments import args
from components import serve_api, serve_grpc
from components.services.rabbitmq import services_rabbitmq
from configurations import conf

api_server = serve_api(debug=args.debug, stage=args.stage)
grpc_server = serve_grpc(debug=args.debug, stage=args.stage)


@api_server.on_event('startup')
async def startup():
    await asyncio.sleep(5)
    services_rabbitmq.RabbitMQService.run()
    print("INFO:\tRabbitMQ Connection established")


@api_server.on_event('shutdown')
def shutdown():
    grpc_server.stop(grace=2)
    print("INFO:\tGRPC Server stopped")
    services_rabbitmq.RabbitMQService.stop()
    print("INFO:\tRabbitMQ Connection closed")


if __name__ == "__main__":
    grpc_server.add_insecure_port(f"[::]:{conf.Proto.GRPC_PORT}")
    grpc_server.start()
    print(f"INFO:\tGRPC Server started at port {conf.Proto.GRPC_PORT}")
    uvicorn.run(api_server, host="0.0.0.0", port=conf.Env.APP_PORT_API)
