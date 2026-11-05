const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {consume} = require('../static/stream.js');

function response(text, step=1){
  const bytes = new TextEncoder().encode(text);
  let offset = 0;
  return new Response(new ReadableStream({
    pull(controller){
      if (offset >= bytes.length) return controller.close();
      controller.enqueue(bytes.slice(offset, offset += step));
    }
  }), {headers:{'content-type':'text/event-stream'}});
}

test('handles UTF-8 and CRLF split across network chunks', async () => {
  const events = [];
  await consume(response('event: delta\r\ndata: {"content":"就诊须知"}\r\n\r\nevent: done\r\ndata: {}\r\n\r\n'),
    (event, data) => events.push([event, data]));
  assert.deepEqual(events, [['delta', {content:'就诊须知'}], ['done', {}]]);
});
test('HTTP error JSON becomes a visible message', async () => {
  await assert.rejects(consume(Response.json({message:'请求过于频繁'}, {status:429}), () => {}), /请求过于频繁/);
});
test('rejects truncated and malformed streams', async () => {
  await assert.rejects(consume(response('event: delta\ndata: {"content":"部分回答"}\n\n'), () => {}), /连接中断/);
  await assert.rejects(consume(response('event: delta\ndata: invalid\n\n'), () => {}));
});
test('error event preserves provider guidance', async () => {
  await assert.rejects(consume(response('event: error\ndata: {"message":"账户余额不足"}\n\n'), () => {}), /余额不足/);
});
test('confirm is a valid terminal event', async () => {
  await consume(response('event: confirm\ndata: {"token":"test"}\n\n'), () => {});
});
test('flush preserves queued text before a done event, even before any timer fires', () => {
  const html = fs.readFileSync(require.resolve('../static/index.html'), 'utf8');
  const finish = html.match(/function finishTyping\(\)\{[\s\S]*?\n\}/)[0];
  const context = {clearInterval(){}, typingTimer:1, typingQueue:['完整','回答'], currentText:'', currentBubble:{}};
  vm.runInNewContext(finish + '\nfinishTyping()', context);
  assert.equal(context.currentBubble.textContent, '完整回答');
  assert.equal(context.typingQueue.length, 0);
});
