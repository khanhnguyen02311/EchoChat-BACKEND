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

// checks.........................: 100.00% ✓ 385      ✗ 0    
// data_received..................: 248 kB  2.4 kB/s
// data_sent......................: 72 kB   707 B/s
// http_req_blocked...............: avg=13.13µs  min=2.77µs   med=5.94µs   max=525.3µs  p(90)=9.13µs   p(95)=12.44µs 
// http_req_connecting............: avg=4.79µs   min=0s       med=0s       max=371.99µs p(90)=0s       p(95)=0s      
// ✗ http_req_duration..............: avg=256.29ms min=165.83ms med=219.94ms max=932.77ms p(90)=347.8ms  p(95)=512.18ms
//   { expected_response:true }...: avg=256.29ms min=165.83ms med=219.94ms max=932.77ms p(90)=347.8ms  p(95)=512.18ms
// ✓ http_req_failed................: 0.00%   ✓ 0        ✗ 385  
// http_req_receiving.............: avg=77.83µs  min=29.71µs  med=71.88µs  max=666.36µs p(90)=99.31µs  p(95)=128.29µs
// http_req_sending...............: avg=33.59µs  min=12.17µs  med=32.04µs  max=131.61µs p(90)=43.19µs  p(95)=58.63µs 
// http_req_tls_handshaking.......: avg=0s       min=0s       med=0s       max=0s       p(90)=0s       p(95)=0s      
// http_req_waiting...............: avg=256.18ms min=165.73ms med=219.82ms max=932.6ms  p(90)=347.67ms p(95)=512.05ms
// http_reqs......................: 385     3.774789/s
// iteration_duration.............: avg=1.25s    min=1.16s    med=1.22s    max=1.93s    p(90)=1.34s    p(95)=1.5s    
// iterations.....................: 379     3.715961/s
// vus............................: 9       min=1      max=9  
// vus_max........................: 100     min=100    max=100


// running (01m42.0s), 000/100 VUs, 379 complete and 9 interrupted iterations
// default ✗ [==>-----------------------------------] 007/100 VUs  01m42.0s/20m00.0s
// ERRO[0103] thresholds on metrics 'http_req_duration' were crossed; at least one has abortOnFail enabled, stopping test prematurely 


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
