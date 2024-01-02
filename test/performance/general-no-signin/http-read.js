import http from "k6/http";
import ws from "k6/ws";
import { check, sleep } from "k6";
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
        {duration: "10m", target: 400}, // Ramp up to 500 users over 10 minutes
        {duration: "30m", target: 400}, // Stay at 500 users for 20 minutes
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
                delayAbortEval: '10s',
            }
        ], // 95% of requests should be below 500ms
    };
} else {  // dev
    BASE_URL = "http://localhost";
    BASE_WS_URL = "ws://localhost";
    HTTP_PORT = 8000;
    WS_PORT = 1323;
    TOKEN_FILENAME = "dev-tokens.json";
    // STAGES = [
    //     {duration: "5m", target: 500}, // Ramp up to 500 users over 5 minutes
    //     {duration: "30m", target: 500}, // Stay at 500 users for 15 minutes
    //     {duration: "2m", target: 0}  // Ramp down to 0 users over 2 minutes
    // ];
    STAGES = [
        {duration: "50m", target: 10000}, 
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
        ], // 95% of requests should be below 0.5s
    };
};

const token_data = new SharedArray('tokenarray', function () {
   const f = JSON.parse(open('./../../' + TOKEN_FILENAME));
   return f; // f must be an array
});

function getRandomSystemUser() {
    // get a random number between 1 and 100
    return Math.floor(Math.random() * 6000) + 1;
}

export const options = {
    stages: STAGES,
    thresholds: THRESHOLDS,
};

export default function () {
    const userId = getRandomSystemUser();
    const accessToken = token_data[userId-1][0]

    const userInfoResponse = http.get(`${BASE_URL}:${HTTP_PORT}/user/me/info/get`, {headers: {Authorization: `Bearer ${accessToken}`}});
    check(userInfoResponse, {"Get user info status is 200": (r) => r.status === 200 && r.timings.duration < 500});
    sleep(4.5 + Math.random()); // average 5s

    const recentGroupsResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/recent`, {headers: {Authorization: `Bearer ${accessToken}`}});
    check(recentGroupsResponse, {"Get recent groups status is 200": (r) => r.status === 200});
    sleep(4.5 + Math.random());

    const groups = JSON.parse(recentGroupsResponse.body);
    const randomGroup = groups[Math.floor(Math.random() * groups.length)];
    const groupId = randomGroup.group_id;

    const groupInfoResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${groupId}/info/get`, {headers: {Authorization: `Bearer ${accessToken}`}});
    check(groupInfoResponse, {"Get group info status is 200": (r) => r.status === 200 && r.timings.duration < 500});
    sleep(4.5 + Math.random());

    const groupParticipantsResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${groupId}/participants`, {headers: {Authorization: `Bearer ${accessToken}`}});
    check(groupParticipantsResponse, {"Get participants status is 200": (r) => r.status === 200 && r.timings.duration < 500});
    sleep(4.5 + Math.random());

    const groupMessagesResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${groupId}/messages/all`, {headers: {Authorization: `Bearer ${accessToken}`}});
    check(groupMessagesResponse, {"Get messages status is 200": (r) => r.status === 200 && r.timings.duration < 500});
    sleep(4.5 + Math.random());
}

// --------------------------------------------
// DEV (breakpoint):
// execution: local
// script: http-read.js
// output: -

// scenarios: (100.00%) 1 scenario, 10000 max VUs, 50m30s max duration (incl. graceful stop):
//       * default: Up to 10000 looping VUs for 50m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)


// ✗ Get user info status is 200
//  ↳  99% — ✓ 3987 / ✗ 9
// ✓ Get recent groups status is 200
// ✗ Get group info status is 200
//  ↳  99% — ✓ 3646 / ✗ 23
// ✗ Get participants status is 200
//  ↳  97% — ✓ 3437 / ✗ 79
// ✗ Get messages status is 200
//  ↳  99% — ✓ 3345 / ✗ 22

// checks.........................: 99.27% ✓ 18239     ✗ 133    
// data_received..................: 40 MB  168 kB/s
// data_sent......................: 6.6 MB 28 kB/s
// http_req_blocked...............: avg=140.48µs min=1.48µs  med=138.09µs max=22.13ms  p(90)=330.03µs p(95)=361.75µs
// http_req_connecting............: avg=93.13µs  min=0s      med=76.74µs  max=22.05ms  p(90)=226.99µs p(95)=250.24µs
// ✗ http_req_duration..............: avg=128.58ms min=1.44ms  med=57.34ms  max=1.24s    p(90)=351.35ms p(95)=501.45ms
//   { expected_response:true }...: avg=128.58ms min=1.44ms  med=57.34ms  max=1.24s    p(90)=351.35ms p(95)=501.45ms
// ✓ http_req_failed................: 0.00%  ✓ 0         ✗ 18372  
// http_req_receiving.............: avg=723.39µs min=15.57µs med=138.37µs max=101.93ms p(90)=1.81ms   p(95)=3.06ms  
// http_req_sending...............: avg=168.01µs min=4.8µs   med=39.09µs  max=112.84ms p(90)=83.2µs   p(95)=98.98µs 
// http_req_tls_handshaking.......: avg=0s       min=0s      med=0s       max=0s       p(90)=0s       p(95)=0s      
// http_req_waiting...............: avg=127.69ms min=1.37ms  med=56.52ms  max=1.23s    p(90)=349.84ms p(95)=499.75ms
// http_reqs......................: 18372  78.047142/s
// iteration_duration.............: avg=25.45s   min=23.11s  med=25.44s   max=28.17s   p(90)=26.41s   p(95)=26.66s  
// iterations.....................: 3221   13.683314/s
// vus............................: 785    min=2       max=785  
// vus_max........................: 10000  min=10000   max=10000


// running (03m55.4s), 00000/10000 VUs, 3221 complete and 785 interrupted iterations
// default ✗ [=>------------------------------------] 00041/10000 VUs  03m55.4s/50m00.0s


// DEV (500):
// execution: local
// script: http-read.js
// output: -

// scenarios: (100.00%) 1 scenario, 500 max VUs, 37m30s max duration (incl. graceful stop):
//       * default: Up to 500 looping VUs for 37m0s over 3 stages (gracefulRampDown: 30s, gracefulStop: 30s)

// ✗ Get user info status is 200
//  ↳  98% — ✓ 38822 / ✗ 618
// ✓ Get recent groups status is 200
// ✗ Get group info status is 200
//  ↳  98% — ✓ 38859 / ✗ 581
// ✗ Get participants status is 200
//  ↳  98% — ✓ 38784 / ✗ 656
// ✗ Get messages status is 200
//  ↳  98% — ✓ 38825 / ✗ 615

// checks.........................: 98.74% ✓ 194730    ✗ 2470  
// data_received..................: 482 MB 215 kB/s
// data_sent......................: 70 MB  31 kB/s
// http_req_blocked...............: avg=122.8µs  min=1.16µs  med=47.62µs max=22.97ms  p(90)=278.63µs p(95)=326.12µs
// http_req_connecting............: avg=81.03µs  min=0s      med=0s      max=22.9ms   p(90)=192.23µs p(95)=229.05µs
// ✓ http_req_duration..............: avg=129.15ms min=1.34ms  med=16.57ms max=9.87s    p(90)=89.13ms  p(95)=146.55ms
//   { expected_response:true }...: avg=129.15ms min=1.34ms  med=16.57ms max=9.87s    p(90)=89.13ms  p(95)=146.55ms
// ✓ http_req_failed................: 0.00%  ✓ 0         ✗ 197200
// http_req_receiving.............: avg=370.97µs min=12.01µs med=84.33µs max=133.92ms p(90)=914.68µs p(95)=1.37ms  
// http_req_sending...............: avg=1.23ms   min=4.88µs  med=29.46µs max=1.07s    p(90)=52.98µs  p(95)=62.71µs 
// http_req_tls_handshaking.......: avg=0s       min=0s      med=0s      max=0s       p(90)=0s       p(95)=0s      
// http_req_waiting...............: avg=127.54ms min=1.28ms  med=16.18ms max=9.84s    p(90)=88.59ms  p(95)=145.78ms
// http_reqs......................: 197200 87.941363/s
// iteration_duration.............: avg=25.65s   min=22.9s   med=25.22s  max=36.55s   p(90)=26.33s   p(95)=31.85s  
// iterations.....................: 39435  17.586043/s
// vus............................: 1      min=1       max=500 
// vus_max........................: 500    min=500     max=500 


// running (37m22.4s), 000/500 VUs, 39435 complete and 5 interrupted iterations
// default ✓ [======================================] 000/500 VUs  37m0s

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