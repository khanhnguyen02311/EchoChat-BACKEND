import http from "k6/http";
import ws from "k6/ws";
import {check, sleep} from "k6";

let BASE_URL = "http://localhost";
let BASE_WS_URL = "ws://localhost";
let HTTP_PORT = 8000;
let WS_PORT = 1323;

if (__ENV.STAGE === "staging") {
    BASE_URL = "https://abcdavid-knguyen.ddns.net";
    HTTP_PORT = 30011;
    WS_PORT = 30012;
}

function getRandomSystemUser() {
    // get a random number between 1 and 100
    const randomUserId = Math.floor(Math.random() * 6000) + 1;
    return `system_user_${randomUserId}`;
}


export const options = {
    stages: [
        { duration: '20m', target: 100 }, // just slowly ramp-up to a HUGE load
    ],
    thresholds: {
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
                delayAbortEval: '0s',
            }
        ], // 95% of requests should be below 0.5s
    },
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

    sleep(1);
}

// DEV: 

// execution: local
// script: signin.js
// output: -

// scenarios: (100.00%) 1 scenario, 100 max VUs, 20m30s max duration (incl. graceful stop):
//       * default: Up to 100 looping VUs for 20m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)


// ✓ Signin status is 200

// checks.........................: 100.00% ✓ 339      ✗ 0    
// data_received..................: 218 kB  2.1 kB/s
// data_sent......................: 64 kB   615 B/s
// http_req_blocked...............: avg=15.91µs  min=2.55µs   med=5.73µs   max=538.14µs p(90)=8.56µs   p(95)=10.87µs 
// http_req_connecting............: avg=6.9µs    min=0s       med=0s       max=411.4µs  p(90)=0s       p(95)=0s      
// ✗ http_req_duration..............: avg=472.25ms min=220.01ms med=329.17ms max=1.74s    p(90)=817.14ms p(95)=1.01s   
//   { expected_response:true }...: avg=472.25ms min=220.01ms med=329.17ms max=1.74s    p(90)=817.14ms p(95)=1.01s   
// ✓ http_req_failed................: 0.00%   ✓ 0        ✗ 339  
// http_req_receiving.............: avg=78.36µs  min=41.68µs  med=72.33µs  max=556µs    p(90)=94.3µs   p(95)=101.05µs
// http_req_sending...............: avg=33.02µs  min=12.57µs  med=31.36µs  max=162.13µs p(90)=41.16µs  p(95)=52.88µs 
// http_req_tls_handshaking.......: avg=0s       min=0s       med=0s       max=0s       p(90)=0s       p(95)=0s      
// http_req_waiting...............: avg=472.14ms min=219.91ms med=329.08ms max=1.74s    p(90)=817.03ms p(95)=1.01s   
// http_reqs......................: 339     3.259829/s
// iteration_duration.............: avg=1.46s    min=1.22s    med=1.32s    max=2.74s    p(90)=1.81s    p(95)=2s      
// iterations.....................: 335     3.221365/s
// vus............................: 9       min=1      max=9  
// vus_max........................: 100     min=100    max=100


// running (01m44.0s), 000/100 VUs, 335 complete and 9 interrupted iterations
// default ✗ [==>-----------------------------------] 009/100 VUs  01m44.0s/20m00.0s
// ERRO[0105] thresholds on metrics 'http_req_duration' were crossed; at least one has abortOnFail enabled, stopping test prematurely 


// STAGING:

// execution: local
// script: signin.js
// output: -

// scenarios: (100.00%) 1 scenario, 100 max VUs, 20m30s max duration (incl. graceful stop):
//       * default: Up to 100 looping VUs for 20m0s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)


// ✓ Signin status is 200

// checks.........................: 100.00% ✓ 52       ✗ 0    
// data_received..................: 58 kB   1.5 kB/s
// data_sent......................: 14 kB   342 B/s
// http_req_blocked...............: avg=13.06ms  min=3.6µs    med=6.87µs   max=234.22ms p(90)=13.2µs   p(95)=141.5ms 
// http_req_connecting............: avg=2.4ms    min=0s       med=0s       max=32.54ms  p(90)=0s       p(95)=30.14ms 
// ✗ http_req_duration..............: avg=664.26ms min=566.39ms med=623.56ms max=1.07s    p(90)=818.55ms p(95)=1s      
//   { expected_response:true }...: avg=664.26ms min=566.39ms med=623.56ms max=1.07s    p(90)=818.55ms p(95)=1s      
// ✓ http_req_failed................: 0.00%   ✓ 0        ✗ 52   
// http_req_receiving.............: avg=95.21µs  min=51.64µs  med=87.16µs  max=202.44µs p(90)=128.03µs p(95)=156.59µs
// http_req_sending...............: avg=43.65µs  min=18.98µs  med=34.55µs  max=284.88µs p(90)=54.76µs  p(95)=70.58µs 
// http_req_tls_handshaking.......: avg=9.97ms   min=0s       med=0s       max=169.88ms p(90)=0s       p(95)=108.98ms
// http_req_waiting...............: avg=664.12ms min=566.27ms med=623.43ms max=1.07s    p(90)=818.39ms p(95)=1s      
// http_reqs......................: 52      1.300246/s
// iteration_duration.............: avg=1.66s    min=1.56s    med=1.62s    max=2.08s    p(90)=1.88s    p(95)=2.02s   
// iterations.....................: 50      1.250237/s
// vus............................: 4       min=1      max=4  
// vus_max........................: 100     min=100    max=100


// running (00m40.0s), 000/100 VUs, 50 complete and 4 interrupted iterations
// default ✗ [>-------------------------------------] 004/100 VUs  00m40.0s/20m00.0s
// ERRO[0041] thresholds on metrics 'http_req_duration' were crossed; at least one has abortOnFail enabled, stopping test prematurely 