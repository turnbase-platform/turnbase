// IMP-M18-09: /ws?instance={pod} reaches the named pod (load-testing-phase-b.md §4.3).
// Usage: node loadtest/check-ws-affinity.mjs   (docker-desktop cluster, two or more ready platform pods)
// For each pod, 100 upgrades carrying a hint for that pod must all land on it (its connection gauge rises
// by exactly the number opened, the others' do not); a hint naming a deleted pod, a malformed hint and a
// request with no hint must be accepted by some live pod. Four sockets per batch: the per-user cap is four.
import { createRequire } from "node:module";
import http from "node:http";
import { execFileSync, spawn } from "node:child_process";
const require = createRequire(new URL("../turnbase-game-tictactoe/package.json", import.meta.url));
const WebSocket = require("ws");

const HOST = "turnbase.localhost";
const FRONT = 18080;
const sh = (...a) => execFileSync("kubectl", a, { encoding: "utf8" }).trim();
const pods = sh("get", "pods", "-l", "app.kubernetes.io/name=platform", "-o", "jsonpath={.items[*].metadata.name}").split(" ");
if (pods.length < 2) throw new Error("need two platform pods");
// The hint is the instance name, `<pod>@<a-b-c-d>:<uuid>` (PodIdentity): the dashed pod address is what the
// proxy resolves through the headless Service.
const ips = Object.fromEntries(
  pods.map((p) => [p, sh("get", "pod", p, "-o", "jsonpath={.status.podIP}").replaceAll(".", "-")]),
);
const forwards = [spawn("kubectl", ["port-forward", "svc/turnbase-frontend", `${FRONT}:8080`], { stdio: "ignore" })];
const mgmt = new Map(pods.map((p, i) => [p, 18081 + i]));
for (const [p, port] of mgmt) forwards.push(spawn("kubectl", ["port-forward", `pod/${p}`, `${port}:8081`], { stdio: "ignore" }));
process.on("exit", () => forwards.forEach((f) => f.kill()));
await new Promise((r) => setTimeout(r, 3000));

const gauge = async (pod) => {
  const text = await (await fetch(`http://127.0.0.1:${mgmt.get(pod)}/actuator/prometheus`)).text();
  return Number(/^turnbase_websocket_connections_active\{[^}]*\} (\S+)/m.exec(text)[1]);
};
const gauges = async () => Object.fromEntries(await Promise.all(pods.map(async (p) => [p, await gauge(p)])));

// fetch() does not let a script set Host, and the proxy routes on it.
const login = (name) =>
  new Promise((resolve, reject) => {
    const body = JSON.stringify({ usernameOrEmail: name, password: "password" });
    const req = http.request(
      { host: "127.0.0.1", port: FRONT, path: "/api/auth/login", method: "POST", headers: { Host: HOST, "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) } },
      (res) => {
        res.resume();
        if (res.statusCode >= 300) return reject(new Error(`login ${name}: ${res.statusCode}`));
        resolve(res.headers["set-cookie"].map((c) => c.split(";")[0]).join("; "));
      },
    );
    req.on("error", reject);
    req.end(body);
  });
const cookie = await login("alice");

const open = (hint) =>
  new Promise((resolve, reject) => {
    const q = hint === null ? "" : `?instance=${encodeURIComponent(hint)}`;
    const ws = new WebSocket(`ws://127.0.0.1:${FRONT}/ws${q}`, { headers: { Cookie: cookie, Origin: `http://${HOST}`, Host: HOST } });
    // The gauge counts STOMP sessions, so the socket counts once the broker has said CONNECTED.
    ws.on("open", () => ws.send("CONNECT\naccept-version:1.2\nheart-beat:0,0\n\n\0"));
    ws.on("message", (m) => m.toString().startsWith("CONNECTED") && resolve(ws));
    ws.on("error", reject);
    ws.on("unexpected-response", (_, res) => reject(new Error(`upgrade refused: ${res.statusCode}`)));
  });
const closeAll = async (sockets) => {
  sockets.forEach((s) => s.close());
  await new Promise((r) => setTimeout(r, 500));
};

let failed = false;
const report = (label, ok, detail = "") => {
  console.log(`${ok ? "PASS" : "FAIL"} ${label} ${detail}`);
  failed ||= !ok;
};

for (const target of pods) {
  let landed = 0;
  let elsewhere = 0;
  for (let batch = 0; batch < 25; batch++) {
    const before = await gauges();
    const sockets = await Promise.all([0, 1, 2, 3].map(() => open(`${target}@${ips[target]}:${crypto.randomUUID()}`)));
    const after = await gauges();
    for (const p of pods) {
      if (p === target) landed += after[p] - before[p];
      else elsewhere += after[p] - before[p];
    }
    await closeAll(sockets);
  }
  report(`hint -> ${target}`, landed === 100 && elsewhere === 0, `landed=${landed} elsewhere=${elsewhere}`);
}

for (const [label, hint] of [
  ["deleted pod", `turnbase-platform-gone-xxxxx@10-1-250-250:${crypto.randomUUID()}`],
  ["no hint", null],
  ["malformed hint", "../../etc"],
]) {
  const before = await gauges();
  const sockets = await Promise.all([0, 1].map(() => open(hint)));
  const after = await gauges();
  const gained = pods.reduce((n, p) => n + after[p] - before[p], 0);
  report(label, gained === 2, `accepted=${gained}/2 ${JSON.stringify(Object.fromEntries(pods.map((p) => [p.slice(-5), after[p] - before[p]])))}`);
  await closeAll(sockets);
}
process.exit(failed ? 1 : 0);
