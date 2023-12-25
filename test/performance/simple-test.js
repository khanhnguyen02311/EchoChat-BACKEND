import http from "k6/http";

export const options = {
    stages: [
        { duration: "30s", target: 100 },    // ramp up
        { duration: "5m", target: 100 },   // stay for 2 minutes
        { duration: "30s", target: 0 },      // ramp down
    ],
};

const BASE_HTTP_URL = "https://test.k6.io";
const BASE_WS_URL = "wss://test.k6.io";

const accounts = new SharedArray("accounts", function() {
    return JSON.parse(open("./accounts.json"));
};

export default function() {
    http.get("http://test.k6.io");
}