/* One parser for chat and confirmation streams; also testable with node --test. */
(function(root){
  async function consume(response, onEvent){
    if (!response) throw new Error('网络异常，请检查连接后重试');
    if (!response.ok || !response.headers.get('content-type')?.includes('text/event-stream')){
      const body = await response.json().catch(() => ({}));
      throw new Error(body.message || body.detail || `请求失败（HTTP ${response.status}）`);
    }
    const reader = response.body.getReader(), decoder = new TextDecoder();
    let buffer = '', terminal = false;
    function dispatch(block){
      let event = 'message', data = [];
      for (const line of block.split('\n')){
        if (line.startsWith('event:')) event = line.slice(6).trim();
        if (line.startsWith('data:')) data.push(line.slice(5).trimStart());
      }
      if (!data.length) return;
      const payload = JSON.parse(data.join('\n'));
      onEvent(event, payload);
      if (event === 'error') throw new Error(payload.message || '请求失败，请重试');
      if (event === 'done' || event === 'confirm') terminal = true;
    }
    try {
      while (!terminal){
        const {done, value} = await reader.read();
        buffer += done ? decoder.decode() : decoder.decode(value, {stream:true});
        // Normalize only complete CRLF pairs, including those split over chunks.
        buffer = buffer.replace(/\r\n/g, '\n');
        let split;
        while (!terminal && (split = buffer.indexOf('\n\n')) >= 0){
          const block = buffer.slice(0, split); buffer = buffer.slice(split + 2);
          dispatch(block);
        }
        if (done){
          if (!terminal) throw new Error('回答连接中断，请重新提问；操作是否成功请先查看记录');
          break;
        }
      }
    } finally {
      await reader.cancel().catch(() => {});
      reader.releaseLock();
    }
  }
  root.ClinicStream = {consume};
  if (typeof module !== 'undefined') module.exports = root.ClinicStream;
})(typeof globalThis !== 'undefined' ? globalThis : window);
