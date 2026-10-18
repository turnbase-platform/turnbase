// Pure-function checks for the STOMP codec and the board helpers. No cluster needed:
//   k6 run loadtest/test/selftest.js
import { check } from 'k6';
import { parseFrames, encodeFrame } from '../lib/stomp.js';
import { winner, isOver, pickEmpty } from '../lib/pair.js';
import { stepper, thresholds } from '../lib/metrics.js';

export const options = { iterations: 1, thresholds: { checks: ['rate==1'] } };

export default function () {
  check(encodeFrame('SEND', { destination: '/app/x' }, '{"a":1}'), {
    'encodeFrame builds a SEND frame': (s) => s === 'SEND\ndestination:/app/x\n\n{"a":1}\0',
  });
  check(parseFrames('\n'), { 'a heart-beat parses to no frames': (f) => f.length === 0 });

  const two = parseFrames('MESSAGE\ndestination:/topic/a\n\n{"type":"X"}\0\nMESSAGE\ndestination:/topic/b\n\n{"type":"Y"}\0');
  check(two, {
    'two frames in one message': (f) => f.length === 2,
    'first frame type and destination': (f) => f[0].msg.type === 'X' && f[0].headers.destination === '/topic/a',
    'second frame type and destination': (f) => f[1].msg.type === 'Y' && f[1].headers.destination === '/topic/b',
  });

  const body = '{"s":"a\\n\\nb"}';
  const raw = body.replace('\\n\\n', '\n\n'); // not valid JSON, only checks that the body survives whole
  const kept = parseFrames('MESSAGE\ndestination:/t\n\n' + raw + '\0');
  check(kept, { 'a body containing a blank line is kept whole': (f) => f.length === 1 && f[0].body === raw });
  const inJson = parseFrames('MESSAGE\ndestination:/t\n\n{"s":"a\\n\\nb"}\0');
  check(inJson, { 'escaped newlines in JSON parse': (f) => f[0].msg.s === 'a\n\nb' });

  check(parseFrames('MESSAGE\ndestination:/t\n\nnot json\0'), {
    'non-JSON body gives msg null': (f) => f.length === 1 && f[0].msg === null && f[0].body === 'not json',
  });

  for (const e of ['', 'O', '-', null]) {
    check(winner(['X', 'X', 'X', e, e, e, e, e, e]), { ['winner on a top row against ' + JSON.stringify(e)]: (w) => w === 'X' });
  }
  check(winner(['X', 'O', 'X', 'O', 'X', 'O', 'O', 'X', 'O']), { 'no winner on a drawn board': (w) => w === null });
  check(isOver(['X', 'O', 'X', 'O', 'X', 'O', 'O', 'X', 'O'], ''), { 'isOver on a full board with no winner': (o) => o === true });
  check(isOver(['', '', '', '', '', '', '', '', ''], ''), { 'a fresh board is not over': (o) => o === false });

  const board = ['X', '', 'O', '', 'X', '', '', 'O', ''];
  let bad = 0;
  for (let i = 0; i < 1000; i++) if (board[pickEmpty(board, '')] !== '') bad++;
  check(bad, { 'pickEmpty never returns an occupied cell': (b) => b === 0 });

  // Stepper: the first `settle` seconds of every segment are tagged warmup; the last segment's tag persists.
  let now = 1000000;
  stepper.configure([{ tag: '10', seconds: 120 }, { tag: '20', seconds: 120 }], 20, () => now, 1000000);
  for (const [at, want] of [[5, 'warmup'], [30, '10'], [125, 'warmup'], [150, '20'], [500, '20']]) {
    now = 1000000 + at * 1000;
    check(stepper.tags(), { ['stepper at ' + at + ' s is ' + want]: (t) => t.step === want });
  }
  stepper.configure([], 0);
  check(stepper.tags(), { 'an unconfigured stepper tags nothing': (t) => Object.keys(t).length === 0 });

  const th = thresholds({ steps: ['10', '20'], abort: true, scale: 0.001 });
  const rtt = th['tb_move_rtt{step:10}'];
  check(rtt, {
    'move_rtt p95 entry aborts after 30 s': (r) => r && r[0].threshold === 'p(95)<0.2' && r[0].abortOnFail === true && r[0].delayAbortEval === '30s',
    'move_rtt p99 entry': (r) => r && r[1].threshold === 'p(99)<0.5',
  });
  check(th, {
    'cold:false game start p95': (t) => t['tb_game_start{step:10,cold:false}'][0].threshold === 'p(95)<1',
    'cold:false game start p99': (t) => t['tb_game_start{step:10,cold:false}'][1].threshold === 'p(99)<2',
    'error rate': (t) => t['tb_op_failed{step:10}'][0].threshold === 'rate<0.00001',
    'second step has its own keys': (t) => Boolean(t['tb_move_rtt{step:20}']),
  });
  const plain = thresholds({ steps: [null], abort: false, scale: 1 });
  check(plain, {
    'untagged keys carry no step': (t) => Array.isArray(t.tb_move_rtt) && t.tb_move_rtt[0] === 'p(95)<200',
    'abort:false yields plain strings': (t) => typeof t['tb_game_start{cold:false}'][1] === 'string',
    'extra entries are merged': (t) => thresholds({ steps: [null], extra: { x: ['count==0'] } }).x[0] === 'count==0',
  });
}
