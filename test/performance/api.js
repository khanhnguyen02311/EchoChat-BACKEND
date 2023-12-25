import http from "k6/http";
import ws from "k6/ws";
import {check, sleep} from "k6";

const BASE_URL = "http://localhost";
const BASE_WS_URL = "ws://localhost";
const HTTP_PORT = 8000;
const WS_PORT = 1323;

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
    const randomUserId = Math.floor(Math.random() * 100) + 1;
    return `system_user_${randomUserId}`;
}


export const options = {
    stages: [
        {duration: "2m", target: 200}, // Ramp up to 100 users over 30 seconds
        {duration: "5m", target: 200}, // Stay at 100 users for 10 minutes
        {duration: "2m", target: 0}  // Ramp down to 0 users over 30 seconds
    ],
};

export default function () {
    // Step 1: Signup
    // const random_name = generateRandomString(10);
    // const email = `${random_name}@email.com`;
    // const signupPayload = {
    //   username: random_name,
    //   email: email,
    //   password: random_name,
    // };
    // const signupResponse = http.post(`${BASE_URL}:${HTTP_PORT}/auth/signup`, signupPayload);
    // check(signupResponse, { "Signup status is 200": (r) => r.status === 200 });

    // Step 2: Signin
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

    sleep(5);

    for (let i = 0; i < 20; i++) {
        const userInfoResponse = http.get(`${BASE_URL}:${HTTP_PORT}/user/me/info/get`, {headers: {Authorization: `Bearer ${accessToken}`}});
        check(userInfoResponse, {"Get user info status is 200": (r) => r.status === 200});
        sleep(5);

        const recentGroupsResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/recent`, {headers: {Authorization: `Bearer ${accessToken}`}});
        check(recentGroupsResponse, {"Get recent groups status is 200": (r) => r.status === 200});
        sleep(5);

        const groups = JSON.parse(recentGroupsResponse.body);
        const randomGroup = groups[Math.floor(Math.random() * groups.length)];
        const groupId = randomGroup.group_id;

        const groupMessagesResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${groupId}/participants`, {headers: {Authorization: `Bearer ${accessToken}`}});
        check(groupMessagesResponse, {"Get participants status is 200": (r) => r.status === 200});
        sleep(5);
    }
}