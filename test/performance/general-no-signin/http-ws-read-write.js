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
    STAGES = [
        {duration: "5m", target: 800}, 
        {duration: "20m", target: 800},
        {duration: "2m", target: 0} 
    ];
    // STAGES = [
    //     {duration: "50m", target: 10000}, 
    // ];
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

        socket.on('error', function (e) {
            if (e.error() != 'websocket: close sent') {
               RateWSOK.add(false);
               // console.log('An unexpected error occured: ', e.error());
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

// scenarios: (100.00%) 1 scenario, 800 max VUs, 27m30s max duration (incl. graceful stop):
//       * default: Up to 800 looping VUs for 27m0s over 3 stages (gracefulRampDown: 30s, gracefulStop: 30s)


// ✓ Get recent groups status is 200
// ✓ Get messages status is 200
// ✓ WebSocket handshake is successful
// ✓ Sent messages are fully received

// checks.........................: 100.00% ✓ 94786      ✗ 0    
// data_received..................: 428 MB  259 kB/s
// data_sent......................: 69 MB   42 kB/s
// http_req_blocked...............: avg=197.12µs min=3.77µs  med=193.95µs max=19.84ms  p(90)=315.75µs p(95)=384.34µs
// http_req_connecting............: avg=126.11µs min=0s      med=122.22µs max=19.76ms  p(90)=202.12µs p(95)=248.57µs
// ✓ http_req_duration..............: avg=141.06ms min=3.21ms  med=9.62ms   max=11.51s   p(90)=75.58ms  p(95)=192.71ms
//   { expected_response:true }...: avg=141.06ms min=3.21ms  med=9.62ms   max=11.51s   p(90)=75.58ms  p(95)=192.71ms
// ✓ http_req_failed................: 0.00%   ✓ 0          ✗ 77868
// http_req_receiving.............: avg=216.43µs min=23.81µs med=79.27µs  max=173.09ms p(90)=509.29µs p(95)=828.58µs
// http_req_sending...............: avg=53.31µs  min=8.73µs  med=40.02µs  max=131.92ms p(90)=64.81µs  p(95)=77.87µs 
// http_req_tls_handshaking.......: avg=0s       min=0s      med=0s       max=0s       p(90)=0s       p(95)=0s      
// http_req_waiting...............: avg=140.79ms min=3.11ms  med=9.36ms   max=11.51s   p(90)=75.19ms  p(95)=192.41ms
// http_reqs......................: 77868   47.192675/s
// iteration_duration.............: avg=2m10s    min=2m4s    med=2m10s    max=2m25s    p(90)=2m14s    p(95)=2m14s   
// iterations.....................: 8435    5.112116/s
// vus............................: 1       min=1        max=800
// vus_max........................: 800     min=800      max=800
// ws_connecting..................: avg=4.68ms   min=1.79ms  med=2.91ms   max=476.16ms p(90)=5.22ms   p(95)=7.15ms  
// ws_msgs_received...............: 963670  584.041777/s
// ws_msgs_sent...................: 276513  167.583451/s
// ✓ ws_ok_rate.....................: 100.00% ✓ 8459       ✗ 0    
// ws_session_duration............: avg=2m0s     min=1m55s   med=2m0s     max=2m10s    p(90)=2m3s     p(95)=2m4s    
// ws_sessions....................: 9050    5.484842/s


// running (27m30.0s), 000/800 VUs, 8435 complete and 615 interrupted iterations
// default ✓ [======================================] 000/800 VUs  27m0s