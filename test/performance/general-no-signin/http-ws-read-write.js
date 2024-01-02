import http from "k6/http";
import ws from "k6/ws";
import {check, sleep} from "k6";
import { SharedArray } from "k6/data";
import {Rate} from 'k6/metrics';

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
        {duration: "10m", target: 1000},
        {duration: "5m", target: 0} 
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
                threshold: 'p(95)<500',
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
    // STAGES = [
    //     {duration: "5m", target: 1000}, 
    //     {duration: "30m", target: 1000},
    //     {duration: "2m", target: 0} 
    // ];
    STAGES = [
        {duration: "50m", target: 10000}, 
    ];
    THRESHOLDS = {
        http_req_failed: [
            {
                threshold: 'rate<0.01',
                abortOnFail: true,
                delayAbortEval: '10s',
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
                delayAbortEval: '10s',
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
    sleep(4.5 + Math.random());

    const groups = JSON.parse(recentGroupsResponse.body);

    const wsResponse = ws.connect(`${BASE_WS_URL}:${WS_PORT}/ws?token=${accessToken}`, {}, function (socket) {
        let sentMessages = 0;
        let successMessages = 0;

        socket.setTimeout(function () {
            socket.close();
        }, 115000 + Math.random() * 10000); // 3 minutes

        socket.on('open', () => {           
            socket.setInterval(function () {
                let randomGroup = groups[Math.floor(Math.random() * groups.length)];
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
               // console.log('An unexpected error occured: ', e.error());
            }
        });

        socket.on('message', function (messsage_data) {
            const json_message = JSON.parse(messsage_data);
            if (json_message.type === "notification") {
                if (Math.random() < 0.1) {
                    socket.send(JSON.stringify({
                        type: "notification-read",
                        data: {
                            group_id: json_message.notification.group_id,
                            type: "GroupEvent",
                        },
                    }));
                    sentMessages += 1;
                    const groupMessagesResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${json_message.notification.group_id}/messages/all`, {headers: {Authorization: `Bearer ${accessToken}`}});
                    check(groupMessagesResponse, {"Get messages status is 200": (r) => r.status === 200});
                }
            } else if (json_message.type === "response" && json_message.status === "success") {
                successMessages += 1;
            }
        });
        socket.on('close', function () {});
    });

    check(wsResponse, { "WebSocket handshake is successful": (r) => r && r.status === 101 }); 
    check(wsResponse, { "Sent messages are fully received": (r) => r.sentMessages == r.successMessages });
    RateWSOK.add(wsResponse && wsResponse.status === 101);
    sleep(4.5 + Math.random());
}

// DEV:

// execution: local
// script: http-ws-read-write.js
// output: -

// scenarios: (100.00%) 1 scenario, 10000 max VUs, 50m30s max duration (incl. graceful stop):
//       * default: Up to 10000 looping VUs for 50m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)


// ✓ Get recent groups status is 200
// ✓ Get messages status is 200
// ✓ WebSocket handshake is successful
// ✓ Sent messages are fully received

// checks.........................: 100.00% ✓ 6934       ✗ 0      
// data_received..................: 33 MB   131 kB/s
// data_sent......................: 6.1 MB  24 kB/s
// http_req_blocked...............: avg=340.69µs min=2µs     med=188.26µs max=41.22ms  p(90)=461.05µs p(95)=786.52µs
// http_req_connecting............: avg=233.73µs min=0s      med=121.47µs max=26.59ms  p(90)=312.08µs p(95)=525.61µs
// ✗ http_req_duration..............: avg=384.34ms min=2.98ms  med=13.82ms  max=9s       p(90)=219.86ms p(95)=4.39s   
//   { expected_response:true }...: avg=384.34ms min=2.98ms  med=13.82ms  max=9s       p(90)=219.86ms p(95)=4.39s   
// ✓ http_req_failed................: 0.00%   ✓ 0          ✗ 6072   
// http_req_receiving.............: avg=255.24µs min=11.27µs med=75.45µs  max=30.19ms  p(90)=550.12µs p(95)=873.08µs
// http_req_sending...............: avg=584.72µs min=6.43µs  med=51.71µs  max=670.11ms p(90)=112.67µs p(95)=220.91µs
// http_req_tls_handshaking.......: avg=0s       min=0s      med=0s       max=0s       p(90)=0s       p(95)=0s      
// http_req_waiting...............: avg=383.5ms  min=2.86ms  med=13.47ms  max=9s       p(90)=219.77ms p(95)=4.39s   
// http_reqs......................: 6072    23.971904/s
// iteration_duration.............: avg=2m10s    min=2m4s    med=2m9s     max=2m15s    p(90)=2m13s    p(95)=2m14s   
// iterations.....................: 410     1.618656/s
// vus............................: 841     min=1        max=841  
// vus_max........................: 10000   min=10000    max=10000
// ws_connecting..................: avg=7.57ms   min=1.58ms  med=3ms      max=597.43ms p(90)=5.81ms   p(95)=11.91ms 
// ws_msgs_received...............: 75226   296.987884/s
// ws_msgs_sent...................: 24208   95.57178/s
// ✓ ws_ok_rate.....................: 100.00% ✓ 431        ✗ 0      
// ws_session_duration............: avg=1m59s    min=1m55s   med=1m59s    max=2m7s     p(90)=2m3s     p(95)=2m4s    
// ws_sessions....................: 1182    4.666467/s


// running (04m13.3s), 00000/10000 VUs, 410 complete and 845 interrupted iterations
// default ✗ [==>-----------------------------------] 00426/10000 VUs  04m13.3s/50m00.0s
// ERRO[0256] thresholds on metrics 'http_req_duration' were crossed; at least one has abortOnFail enabled, stopping test prematurely 