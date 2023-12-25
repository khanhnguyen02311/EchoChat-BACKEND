import http from "k6/http";
import ws from "k6/ws";
import { check, sleep } from "k6";

const BASE_URL = "http://localhost";
const BASE_WS_URL = "ws://localhost";
const HTTP_PORT = 8000;
const WS_PORT = 1323;
var current_user = 1;

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
  // get a random number between 1 and 100
  const randomUserId = Math.floor(Math.random() * 100) + 1;
  return `system_user_${randomUserId}`;
}


export const options = {
  stages: [
    { duration: "30s", target: 20 }, // Ramp up to 100 users over 30 seconds
    { duration: "5m", target: 20 }, // Stay at 100 users for 5 minutes
    { duration: "30s", target: 0 }  // Ramp down to 0 users over 30 seconds
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

  const timeStart = new Date().getTime();
  const signinResponse = http.post(`${BASE_URL}:${HTTP_PORT}/auth/signin`, signinPayload);
  if (!check(signinResponse, { "Signin status is 200": (r) => r.status === 200 })) {
    const timeEnd = new Date().getTime();
    const time = timeEnd - timeStart;
    console.log(`Failed signin took ${time}ms`);
  }

  const accessToken = JSON.parse(signinResponse.body).access_token;

  // Step 4: Get recent chat groups
  const recentGroupsResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/recent`, { headers: { Authorization: `Bearer ${accessToken}` } });
  check(recentGroupsResponse, { "Get recent groups status is 200": (r) => r.status === 200 });

  const groups = JSON.parse(recentGroupsResponse.body);
  const randomGroup = groups[Math.floor(Math.random() * groups.length)];
  const groupId = randomGroup.group_id;

  const messagePayload = JSON.stringify({
    type: "message-new",
    data: {
      group_id: groupId,
      type: "Message",
      content: `random_content_${generateRandomString(5)}`,
    },
  });

  // Step 3: Connect to WS
  const wsResponse = ws.connect(`${BASE_WS_URL}:${WS_PORT}/ws?token=${accessToken}`, {}, function (socket) {
    socket.on('open', () => {
      socket.send(messagePayload);
      sleep(5);
      socket.send(messagePayload);
      sleep(5);
      socket.send(messagePayload);
      sleep(5);
      socket.send(messagePayload);
      sleep(5);
      socket.send(messagePayload);
      sleep(5);
      socket.close();
    });
    socket.on('message', (data) => console.log('Message received: ', data));
    socket.on('close', () => {});

    socket.setTimeout(function () {
      console.log('5 seconds passed, closing the socket');
      socket.close();
    }, 5000);
  });
  check(wsResponse, { "WebSocket handshake is successful": (r) => r && r.status === 101 }); 

  const groupMessagesResponse = http.get(`${BASE_URL}:${HTTP_PORT}/chat/group/${groupId}/messages/all`, { headers: { Authorization: `Bearer ${accessToken}` } });
  check(groupMessagesResponse, { "Get group messages status is 200": (r) => r.status === 200 });

  // Sleep for a short duration between steps
  sleep(5);
}