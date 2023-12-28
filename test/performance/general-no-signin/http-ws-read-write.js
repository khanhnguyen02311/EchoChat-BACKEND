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
                delayAbortEval: '5s',
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
        {duration: "5m", target: 500}, 
        {duration: "15m", target: 500},
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
                threshold: 'p(95)<500',
                abortOnFail: true,
                delayAbortEval: '5s',
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

    const recentGroupsResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/recent`, {headers: {Authorization: `Bearer ${accessToken}`}});
    check(recentGroupsResponse, {"Get recent groups status is 200": (r) => r.status === 200});
    sleep(5);

    const groups = JSON.parse(recentGroupsResponse.body);

    while (true) {
        const wsResponse = ws.connect(`${BASE_WS_URL}:${WS_PORT}/ws?token=${accessToken}`, {}, function (socket) {
            let sentMessages = 0;
            let successMessages = 0;
    
            socket.setTimeout(function () {
                socket.close();
            }, 60000);
    
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
                    if (Math.random() < 0.2) {
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

        sleep(4.5 + Math.random());
    }
}
