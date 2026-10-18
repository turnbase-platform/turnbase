// Pure-function checks for the STOMP codec and the board helpers. No cluster needed:
//   k6 run loadtest/test/selftest.js
import { check } from 'k6';
import { parseFrames, encodeFrame } from '../lib/stomp.js';
import { winner, isOver, pickEmpty } from '../lib/pair.js';

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
}
