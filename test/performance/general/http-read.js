import http from "k6/http";
import ws from "k6/ws";
import {check, sleep} from "k6";

let BASE_URL;
let BASE_WS_URL;
let HTTP_PORT;
let WS_PORT;
let SIGNIN_WAIT;
let STAGES;
let THRESHOLDS;

if (__ENV.STAGE === "staging") {
    BASE_URL = "https://abcdavid-knguyen.ddns.net";
    BASE_WS_URL = "wss://abcdavid-knguyen.ddns.net";
    HTTP_PORT = 30011;
    WS_PORT = 3001;
    SIGNIN_WAIT = 600;
    STAGES = [
        {duration: "10m", target: 500}, // Ramp up to 500 users over 10 minutes
        {duration: "25m", target: 500}, // Stay at 500 users for 20 minutes
        {duration: "2m", target: 0}  // Ramp down to 0 users over 2 minutes
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
                delayAbortEval: '5s',
            }
        ], // 95% of requests should be below 1s
    };
} else {  // dev
    BASE_URL = "http://localhost";
    BASE_WS_URL = "ws://localhost";
    HTTP_PORT = 8000;
    WS_PORT = 1323;
    SIGNIN_WAIT = 300;
    STAGES = [
        {duration: "5m", target: 500}, // Ramp up to 500 users over 5 minutes
        {duration: "15m", target: 500}, // Stay at 500 users for 15 minutes
        {duration: "2m", target: 0}  // Ramp down to 0 users over 2 minutes
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

// function generateRandomString(length) {
//     const characters = "abcdefghijklmnopqrstuvwxyz";
//     let result = "";
//     const charactersLength = characters.length;
//     for (let i = 0; i < length; i += 1) {
//         result += characters.charAt(Math.floor(Math.random() * charactersLength));
//     }
//     return result;
// }

function getRandomSystemUser() {
    // get a random number between 1 and 100
    const randomUserId = Math.floor(Math.random() * 6000) + 1;
    return `system_user_${randomUserId}`;
}

export const options = {
    stages: STAGES,
    thresholds: THRESHOLDS,
};

export default function () {
    const username = getRandomSystemUser();
    // const username = `system_user_${current_user}`;
    // current_user += 1;

    const signinPayload = JSON.stringify({
        username_or_email: username,
        password: "system_user_password",
    });

    const signinResponse = http.post(`${BASE_URL}:${HTTP_PORT}/auth/signin`, signinPayload);
    check(signinResponse, {"Signin status is 200": (r) => r.status === 200});

    const accessToken = JSON.parse(signinResponse.body).access_token;

    sleep(SIGNIN_WAIT); // sleep until all the users sign in

    while (true) {
        const userInfoResponse = http.get(`${BASE_URL}:${HTTP_PORT}/user/me/info/get`, {headers: {Authorization: `Bearer ${accessToken}`}});
        check(userInfoResponse, {"Get user info status is 200": (r) => r.status === 200});
        sleep(4.5 + Math.random()); // average 5s

        const recentGroupsResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/recent`, {headers: {Authorization: `Bearer ${accessToken}`}});
        check(recentGroupsResponse, {"Get recent groups status is 200": (r) => r.status === 200});
        sleep(4.5 + Math.random());

        const groups = JSON.parse(recentGroupsResponse.body);
        const randomGroup = groups[Math.floor(Math.random() * groups.length)];
        const groupId = randomGroup.group_id;

        const groupInfoResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${groupId}/info/get`, {headers: {Authorization: `Bearer ${accessToken}`}});
        check(groupInfoResponse, {"Get group info status is 200": (r) => r.status === 200});
        sleep(4.5 + Math.random());

        const groupParticipantsResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${groupId}/participants`, {headers: {Authorization: `Bearer ${accessToken}`}});
        check(groupParticipantsResponse, {"Get participants status is 200": (r) => r.status === 200});
        sleep(4.5 + Math.random());

        const groupMessagesResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${groupId}/messages/all`, {headers: {Authorization: `Bearer ${accessToken}`}});
        check(groupMessagesResponse, {"Get messages status is 200": (r) => r.status === 200});
        sleep(4.5 + Math.random());
    }
}

// --------------------------------------------
// DEV:

// execution: local
// script: http-read.js
// output: -

// scenarios: (100.00%) 1 scenario, 600 max VUs, 22m30s max duration (incl. graceful stop):
//         * default: Up to 600 looping VUs for 22m0s over 3 stages (gracefulRampDown: 30s, gracefulStop: 30s)


//     ✓ Signin status is 200
//     ✓ Get user info status is 200
//     ✓ Get recent groups status is 200
//     ✓ Get group info status is 200
//     ✓ Get participants status is 200
//     ✓ Get messages status is 200

//     checks.........................: 100.00% ✓ 26784     ✗ 0    
//     data_received..................: 47 MB   70 kB/s
//     data_sent......................: 13 MB   19 kB/s
//     http_req_blocked...............: avg=152.09µs min=1.28µs  med=161.61µs max=34.23ms p(90)=330.49µs p(95)=375.9µs 
//     http_req_connecting............: avg=40.72µs  min=0s      med=0s       max=34.13ms p(90)=186.81µs p(95)=229.45µs
// ✗ http_req_duration..............: avg=99.88ms  min=1.5ms   med=30.69ms  max=1.63s   p(90)=274.54ms p(95)=507.07ms
//     { expected_response:true }...: avg=99.88ms  min=1.5ms   med=30.69ms  max=1.63s   p(90)=274.54ms p(95)=507.07ms
// ✓ http_req_failed................: 0.00%   ✓ 0         ✗ 26784
//     http_req_receiving.............: avg=388.91µs min=12.98µs med=102.64µs max=69.83ms p(90)=1.04ms   p(95)=1.54ms  
//     http_req_sending...............: avg=1.09ms   min=4.35µs  med=50.87µs  max=95.99ms p(90)=2.64ms   p(95)=4.79ms  
//     http_req_tls_handshaking.......: avg=0s       min=0s      med=0s       max=0s      p(90)=0s       p(95)=0s      
//     http_req_waiting...............: avg=98.4ms   min=1.39ms  med=29.13ms  max=1.63s   p(90)=274.27ms p(95)=504.53ms
//     http_reqs......................: 26784   39.978982/s
//     vus............................: 600     min=2       max=600
//     vus_max........................: 600     min=600     max=600


// running (11m10.0s), 000/600 VUs, 0 complete and 600 interrupted iterations
// default ✗ [==================>-------------------] 073/600 VUs  11m10.0s/22m00.0s
// ERRO[0672] thresholds on metrics 'http_req_duration' were crossed; at least one has abortOnFail enabled, stopping test prematurely 

// --------------------------------------------
// STAGING: 

// execution: local
// script: http-read.js
// output: -

// scenarios: (100.00%) 1 scenario, 500 max VUs, 37m30s max duration (incl. graceful stop):
//       * default: Up to 500 looping VUs for 37m0s over 3 stages (gracefulRampDown: 30s, gracefulStop: 30s)

// ✓ Signin status is 200
// ✗ Get user info status is 200
//  ↳  99% — ✓ 25129 / ✗ 3
// ✗ Get recent groups status is 200
//  ↳  99% — ✓ 25024 / ✗ 1
// ✗ Get group info status is 200
//  ↳  99% — ✓ 24921 / ✗ 1
// ✗ Get participants status is 200
//  ↳  99% — ✓ 24823 / ✗ 1
// ✗ Get messages status is 200
//  ↳  99% — ✓ 24724 / ✗ 2

// checks.........................: 99.99% ✓ 125122   ✗ 8     
// data_received..................: 243 MB 108 kB/s
// data_sent......................: 50 MB  22 kB/s
// http_req_blocked...............: avg=2.48ms   min=0s     med=5.68µs   max=1.2s     p(90)=8.18µs   p(95)=9.89µs  
// http_req_connecting............: avg=611.87µs min=0s     med=0s       max=1.05s    p(90)=0s       p(95)=0s      
// ✓ http_req_duration..............: avg=177.15ms min=0s     med=120.67ms max=1m0s     p(90)=276.35ms p(95)=466.37ms
//   { expected_response:true }...: avg=173.8ms  min=59.1ms med=120.67ms max=2.6s     p(90)=276.23ms p(95)=466.06ms
// ✓ http_req_failed................: 0.00%  ✓ 8        ✗ 125122
// http_req_receiving.............: avg=72.49µs  min=0s     med=70.29µs  max=1.94ms   p(90)=100.71µs p(95)=111.74µs
// http_req_sending...............: avg=28.96µs  min=0s     med=27.82µs  max=825.38µs p(90)=39.7µs   p(95)=44.53µs 
// http_req_tls_handshaking.......: avg=1.86ms   min=0s     med=0s       max=734.28ms p(90)=0s       p(95)=0s      
// http_req_waiting...............: avg=177.05ms min=0s     med=120.57ms max=1m0s     p(90)=276.21ms p(95)=466.27ms
// http_reqs......................: 125130 55.61331/s
// iteration_duration.............: avg=24m59s   min=24m59s med=24m59s   max=24m59s   p(90)=24m59s   p(95)=24m59s  
// iterations.....................: 1      0.000444/s
// vus............................: 1      min=1      max=500 
// vus_max........................: 500    min=500    max=500 


// running (37m30.0s), 000/500 VUs, 1 complete and 500 interrupted iterations
// default ✓ [======================================] 001/500 VUs  37m0s