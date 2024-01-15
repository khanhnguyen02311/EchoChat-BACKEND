import http from "k6/http";
import ws from "k6/ws";
import {check, sleep} from "k6";
import { SharedArray } from "k6/data";

let BASE_URL;
let BASE_WS_URL;
let HTTP_PORT;
let WS_PORT;
let TOKEN_FILENAME;
let STAGES;
let THRESHOLDS;

if (__ENV.STAGE === "staging") {
    BASE_URL = "https://abcdavid-knguyen.ddns.net";
    BASE_WS_URL = "wss://abcdavid-knguyen.ddns.net";
    HTTP_PORT = 30011;
    WS_PORT = 30013;
    TOKEN_FILENAME = "staging-tokens.json";
    STAGES = [
        {duration: "30m", target: 10000}
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
    };
} else {  // dev
    BASE_URL = "http://localhost";
    BASE_WS_URL = "ws://localhost";
    HTTP_PORT = 8000;
    WS_PORT = 1323;
    TOKEN_FILENAME = "dev-tokens.json";
    STAGES = [
        {duration: "30m", target: 10000}, 
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
                delayAbortEval: '10s',
            }
        ], // 95% of requests should be below 0.5s
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

    const wsResponse = ws.connect(`${BASE_WS_URL}:${WS_PORT}/ws?token=${accessToken}`, {}, function (socket) {
        let sentMessages = 0;
        let successMessages = 0;

        socket.setTimeout(function () {
            socket.close();
        }, 12000000);  // wait until end of test

        socket.on('open', () => {});
        socket.on('message', function (messsage_data) {});
        socket.on('close', function () {});
    });

    check(wsResponse, { "WebSocket handshake is successful": (r) => r && r.status === 101 }); 
}

// execution: local
// script: ws-connect.js
// output: -

// scenarios: (100.00%) 1 scenario, 10000 max VUs, 30m30s max duration (incl. graceful stop):
//       * default: Up to 10000 looping VUs for 30m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)

// WARN[1831] No script iterations fully finished, consider making the test duration longer 

// ✓ WebSocket handshake is successful

// data_received.......: 1.3 MB 705 B/s
// data_sent...........: 4.2 MB 2.3 kB/s
// ✓ http_req_duration...: avg=0s     min=0s     med=0s    max=0s       p(90)=0s     p(95)=0s 
// ✓ http_req_failed.....: 0.00%  ✓ 0        ✗ 0      
// vus.................: 9999   min=3      max=9999 
// vus_max.............: 10000  min=10000  max=10000
// ws_connecting.......: avg=3.27ms min=1.87ms med=3.2ms max=130.54ms p(90)=3.78ms p(95)=4ms
// ws_sessions.........: 9999   5.463451/s


// running (30m30.2s), 00000/10000 VUs, 0 complete and 9999 interrupted iterations
// default ✓ [======================================] 08972/10000 VUs  30m0s