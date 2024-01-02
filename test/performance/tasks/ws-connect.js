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
        {duration: "200m", target: 10000}
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
