import http from "k6/http";
import ws from "k6/ws";
import {check, sleep} from "k6";
import {Rate} from 'k6/metrics';
import { SharedArray } from "k6/data";

let BASE_URL;
let BASE_WS_URL;
let HTTP_PORT;
let WS_PORT;
let TOKEN_FILENAME;
let STAGES;
let THRESHOLDS;
export const RateWSOK = new Rate('ws_ok_rate');

if (__ENV.STAGE === "staging") {
    BASE_URL = "https://abcdavid-knguyen.ddns.net";
    BASE_WS_URL = "wss://abcdavid-knguyen.ddns.net";
    HTTP_PORT = 30011;
    WS_PORT = 30013;
    TOKEN_FILENAME = "staging-tokens.json";
    STAGES = [
        {duration: "5m", target: 1000},
        {duration: "30m", target: 1000},
        {duration: "2m", target: 0} 
    ];
    THRESHOLDS = {
        http_req_failed: [
            {
                threshold: 'rate<0.01',
                abortOnFail: true,
                delayAbortEval: '5s',
            }
        ], // http errors should be less than 1%
        http_req_duration: [
            {
                threshold: 'p(95)<1000',
                abortOnFail: true,
                delayAbortEval: '15s',
            }
        ], // 95% of requests should be below 1s
        ws_ok_rate: [
         {
             threshold: 'rate>0.99',
             abortOnFail: true,
             delayAbortEval: '15s',
         }
     ],
    };
} else {  // dev
    BASE_URL = "http://localhost";
    BASE_WS_URL = "ws://localhost";
    HTTP_PORT = 8000;
    WS_PORT = 1323;
    TOKEN_FILENAME = "dev-tokens.json";
    STAGES = [
      {duration: "10m", target: 1000},
      {duration: "20m", target: 1000},
      {duration: "2m", target: 0} 
   ];
    // STAGES = [
    //     {duration: "60m", target: 10000}, 
    // ];
    THRESHOLDS = {
        http_req_failed: [
            {
                threshold: 'rate<0.01',
                abortOnFail: true,
                delayAbortEval: '5s',
            }
        ], // http errors should be less than 1%
        http_req_duration: [
            {
                threshold: 'p(95)<500',
                abortOnFail: true,
                delayAbortEval: '10s',
            }
        ], // 95% of requests should be below 0.5s
        ws_ok_rate: [
            {
                threshold: 'rate>0.99',
                abortOnFail: true,
                delayAbortEval: '15s',
            }
        ],
    };
};

const token_data = new SharedArray('tokenarray', function () {
   const f = JSON.parse(open('./../../' + TOKEN_FILENAME));
   return f; // f must be an array
});

function generateRandomString(length) {
    const characters = "abcdefghijklmnopqrstuvwxyz";
    let result = "";
    const charactersLength = characters.length;
    for (let i = 0; i < length; i += 1) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}

function getRandomSystemUser() {
    return Math.floor(Math.random() * 6000) + 1;
}

export const options = {
    stages: STAGES,
    thresholds: THRESHOLDS,
};

export default function () {
    const userId = getRandomSystemUser();
    const accessToken = token_data[userId-1][0];

    const recentGroupsResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/recent`, {headers: {Authorization: `Bearer ${accessToken}`}});
    check(recentGroupsResponse, {"Get recent groups status is 200": (r) => r.status === 200});
    sleep(2 + Math.random());

    const groups = JSON.parse(recentGroupsResponse.body);

    while (true) {
        const wsResponse = ws.connect(`${BASE_WS_URL}:${WS_PORT}/ws?token=${accessToken}`, {}, function (socket) {
            let sentMessages = 0;
            let successMessages = 0;
    
            socket.setTimeout(function () {
                socket.close();
            }, 115000 + Math.random() * 10000);  // average 2 minutes
    
            socket.on('open', () => {           
                socket.setInterval(function () {
                    // console.log(groups.length);
                    let randomGroup = groups[Math.floor(Math.random() * groups.length)];
                    // console.log(`Sending message to group ${randomGroup}`)
                    socket.send(JSON.stringify({
                        type: "message-new",
                        data: {
                            group_id: randomGroup.group_id,
                            type: "Message",
                            content: `random_content_${generateRandomString(6)}`,
                        },
                    }));
                    sentMessages += 1;
                }, 4500 + Math.random() * 1000);
            });

            socket.on('error', function (e) {
               if (e.error() != 'websocket: close sent') {
                  RateWSOK.add(false);
                  console.log('WS unexpected error happened: ', e.error());
               }
             });
    
            socket.on('message', function (messsage_data) {
                const json_message = JSON.parse(messsage_data);
                // if (json_message.type === "notification") {
                //     if (Math.random() < 0.1) {  // 10% chance to read notification
                //         socket.send(JSON.stringify({
                //             type: "notification-read",
                //             data: {
                //                 group_id: json_message.notification.group_id,
                //                 type: "GroupEvent",
                //             },
                //         }));
                //         sentMessages += 1;
                //     }
                // } else 
                if (json_message.type === "response" && json_message.status === "success") {
                    successMessages += 1;
                }
            });
            socket.on('close', function () {});
        });
    
        check(wsResponse, { "WebSocket handshake is successful": (r) => r && r.status === 101 }); 
        if (!wsResponse || wsResponse.status !== 101) {
            console.log("WS error happened: ", wsResponse.error);
        }
        check(wsResponse, { "Sent messages are fully received": (r) => r.sentMessages == r.successMessages });
        RateWSOK.add(wsResponse && wsResponse.status === 101);
        sleep(2 + Math.random());
    }
}


// DEV (1000):



// DEV (breakpoint):

// ✓ Get recent groups status is 200
// ✗ WebSocket handshake is successful
//  ↳  98% — ✓ 2832 / ✗ 33
// ✓ Sent messages are fully received

// checks.........................: 99.53% ✓ 7035       ✗ 33     
// data_received..................: 65 MB  163 kB/s
// data_sent......................: 8.7 MB 22 kB/s
// http_req_blocked...............: avg=283.92µs min=114.09µs med=233µs    max=31.31ms  p(90)=337.23µs p(95)=367.27µs
// http_req_connecting............: avg=210.13µs min=72.77µs  med=161.95µs max=31.25ms  p(90)=239.78µs p(95)=262.19µs
// ✓ http_req_duration..............: avg=139.81ms min=19.49ms  med=114.6ms  max=1.12s    p(90)=275.59ms p(95)=361.6ms 
//   { expected_response:true }...: avg=139.81ms min=19.49ms  med=114.6ms  max=1.12s    p(90)=275.59ms p(95)=361.6ms 
// ✓ http_req_failed................: 0.00%  ✓ 0          ✗ 1338   
// http_req_receiving.............: avg=86.33µs  min=40.08µs  med=75.78µs  max=1.24ms   p(90)=111.43µs p(95)=148.58µs
// http_req_sending...............: avg=63.04µs  min=19.9µs   med=58.84µs  max=554.01µs p(90)=87.57µs  p(95)=96.69µs 
// http_req_tls_handshaking.......: avg=0s       min=0s       med=0s       max=0s       p(90)=0s       p(95)=0s      
// http_req_waiting...............: avg=139.66ms min=19.39ms  med=114.43ms max=1.12s    p(90)=275.44ms p(95)=361.47ms
// http_reqs......................: 1338   3.333711/s
// vus............................: 1338   min=2        max=1338 
// vus_max........................: 10000  min=10000    max=10000
// ws_connecting..................: avg=3.48ms   min=119.71µs med=2.45ms   max=647.99ms p(90)=3.71ms   p(95)=4.28ms  
// ws_msgs_received...............: 245876 612.615458/s
// ws_msgs_sent...................: 50461  125.726743/s
// ✗ ws_ok_rate.....................: 68.10% ✓ 2832       ✗ 1326   
// ws_session_duration............: avg=1m30s    min=142.89µs med=1m55s    max=2m5s     p(90)=2m3s     p(95)=2m4s    
// ws_sessions....................: 2865   7.138327/s


// running (06m41.4s), 00000/10000 VUs, 0 complete and 1338 interrupted iterations
// default ✗ [====>---------------------------------] 00033/10000 VUs  06m41.4s/50m00.0s