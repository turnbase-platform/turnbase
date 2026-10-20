// A small STOMP 1.2 client over k6/websockets. Port of the client in .claude/skills/run-turnbase/driver.mjs.
import { WebSocket } from 'k6/websockets';

const BUFFER_MAX = 256;
const HEARTBEAT_MS = 4000;

export function encodeFrame(command, headers, body) {
  let s = command + '\n';
  for (const k of Object.keys(headers || {})) s += k + ':' + headers[k] + '\n';
  return s + '\n' + (body || '') + '\0';
}

// One WebSocket message can carry several frames and leading heart-beat newlines.
export function parseFrames(data) {
  const frames = [];
  for (const raw of String(data).split('\0')) {
    const text = raw.replace(/^\n+/, '');
    if (!text) continue;
    const cut = text.indexOf('\n\n');
    const head = cut < 0 ? text : text.slice(0, cut);
    const body = cut < 0 ? '' : text.slice(cut + 2);
    const lines = head.split('\n');
    const headers = {};
    for (const l of lines.slice(1)) {
      const i = l.indexOf(':');
      if (i > 0 && headers[l.slice(0, i)] === undefined) headers[l.slice(0, i)] = l.slice(i + 1);
    }
    let msg = null;
    try { msg = JSON.parse(body); } catch (_) { /* not JSON */ }
    frames.push({ command: lines[0], headers, body, msg });
  }
  return frames;
}

function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.floor(Math.random() * 16);
    return (c === 'x' ? r : (r & 3) | 8).toString(16);
  });
}

function codeError(message, code) {
  const e = new Error(message);
  e.code = code;
  return e;
}

export class StompClient {
  constructor(url, headers, hooks) {
    this.url = url;
    this.headers = headers || {};
    this.hooks = hooks || {};
    this.buffer = [];
    this.waiters = [];
    this.open = false;
    this.closing = false;
    this.nextSub = 0;
  }

  connect(timeoutMs) {
    return new Promise((resolve, reject) => {
      let settled = false;
      const settle = (fn, v) => { if (!settled) { settled = true; clearTimeout(timer); fn(v); } };
      const timer = setTimeout(() => {
        this.closing = true; // our own abort: not an "unexpected" close
        try { this.ws.close(); } catch (_) { /* already closed */ }
        settle(reject, codeError('STOMP connect timed out', 'connect_timeout'));
      }, timeoutMs);
      const ws = new WebSocket(this.url, null, { headers: this.headers });
      this.ws = ws;
      ws.onopen = () => {
        // The server closes a client that does not heart-beat (the one thing driver.mjs comments on).
        ws.send(encodeFrame('CONNECT', { 'accept-version': '1.2', 'heart-beat': '10000,10000' }, ''));
        this.hb = setInterval(() => { if (this.open || !this.closing) ws.send('\n'); }, HEARTBEAT_MS);
      };
      ws.onmessage = (e) => {
        const t = Date.now(); // arrival time, once per WebSocket message, before parsing
        for (const f of parseFrames(e.data)) {
          f.t = t;
          if (f.command === 'CONNECTED') { this.open = true; settle(resolve, this); continue; }
          if (f.command === 'ERROR') {
            settle(reject, codeError('STOMP ERROR: ' + (f.headers.message || f.body), 'stomp_error'));
            this.dispatch(f);
            this.close();
            continue;
          }
          this.dispatch(f);
        }
      };
      ws.onerror = () => { /* followed by onclose */ };
      ws.onclose = () => {
        clearInterval(this.hb);
        const wasOpen = this.open;
        this.open = false;
        settle(reject, codeError('socket closed before CONNECTED', 'ws_closed'));
        for (const w of this.waiters.splice(0)) { clearTimeout(w.timer); w.reject(codeError('socket closed', 'ws_closed')); }
        if (!this.closing) {
          this.closing = true;
          if (wasOpen && this.hooks.onUnexpectedClose) this.hooks.onUnexpectedClose();
        }
      };
    });
  }

  dispatch(f) {
    const i = this.waiters.findIndex((w) => w.pred(f));
    if (i >= 0) {
      const [w] = this.waiters.splice(i, 1);
      clearTimeout(w.timer);
      w.resolve(f); // a frame handed to a waiter is not buffered
      return;
    }
    this.buffer.push(f);
    if (this.buffer.length > BUFFER_MAX) this.buffer.shift();
  }

  subscribe(destination) {
    const id = 'sub-' + (this.nextSub++);
    this.ws.send(encodeFrame('SUBSCRIBE', { id, destination }, ''));
    return id;
  }

  // Resolves with the subscription id once the server's RECEIPT says the subscription is registered (a frame
  // sent or broadcast before that can miss it). The waiter exists before the frame is sent, so the RECEIPT
  // cannot be missed. Rejects with `subscribe_timeout`.
  subscribeConfirmed(destination, timeoutMs) {
    const id = 'sub-' + (this.nextSub++);
    const receipt = 'rcpt-' + id;
    const confirmed = this.waitFor((f) => f.command === 'RECEIPT' && f.headers['receipt-id'] === receipt,
      timeoutMs, 'subscribe_timeout');
    this.ws.send(encodeFrame('SUBSCRIBE', { id, destination, receipt }, ''));
    return confirmed.then(() => id);
  }

  unsubscribe(id) {
    if (this.open && !this.closing) this.ws.send(encodeFrame('UNSUBSCRIBE', { id }, ''));
  }

  send(destination, type, payload) {
    const body = JSON.stringify({ type, correlationId: uuid(), payload: payload || {} });
    const frame = encodeFrame('SEND', { destination, 'content-type': 'application/json' }, body);
    const t0 = Date.now();
    this.ws.send(frame);
    return t0;
  }

  // Scans the buffer first and removes the first match; otherwise waits. Rejects with `.code`.
  waitFor(pred, timeoutMs, code) {
    const i = this.buffer.findIndex(pred);
    if (i >= 0) return Promise.resolve(this.buffer.splice(i, 1)[0]);
    if (!this.open) return Promise.reject(codeError('socket closed', 'ws_closed'));
    return new Promise((resolve, reject) => {
      const w = { pred, resolve, reject };
      w.timer = setTimeout(() => {
        const j = this.waiters.indexOf(w);
        if (j >= 0) this.waiters.splice(j, 1);
        reject(codeError('timed out waiting for a frame', code || 'timeout'));
      }, timeoutMs);
      this.waiters.push(w);
    });
  }

  clear() { this.buffer = []; }

  close() {
    this.closing = true;
    this.open = false;
    clearInterval(this.hb);
    try { this.ws.close(); } catch (_) { /* already closed */ }
  }
}
