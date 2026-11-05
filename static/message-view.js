/* Display-only formatting. Never changes requests, stored messages or rule text.
   Build DOM with text nodes, not HTML, so model responses cannot inject markup. */
(function(){
  function inline(parent, text){
    for (const part of text.split(/(\*\*[^*\n]+\*\*)/g)){
      if (part.startsWith('**') && part.endsWith('**') && part.length > 4){
        const strong = document.createElement('strong');
        strong.textContent = part.slice(2, -2); parent.appendChild(strong);
      } else parent.appendChild(document.createTextNode(part));
    }
  }
  function format(bubble){
    // Streaming continues to use the existing plain-text typing renderer.
    if (bubble.querySelector('.cursor') || bubble.querySelector('.message-content')) return;
    const textNodes = [...bubble.childNodes].filter(node => node.nodeType === Node.TEXT_NODE);
    const text = textNodes.map(node => node.textContent).join('');
    if (!text.trim()) return;
    const content = document.createElement('div'); content.className = 'message-content';
    let section;
    function newSection(){
      section = document.createElement('section'); section.className = 'answer-section';
      content.appendChild(section);
    }
    newSection();
    for (const paragraph of text.split(/\n\s*\n/)){
      const match = paragraph.match(/^(?:\*\*([^*\n]{1,60})\*\*|#{1,6}\s+([^\n]+))(?:\s*\n|\s*$|\s*(?=\S))/);
      let rest = paragraph;
      if (match){
        if (section.childNodes.length) newSection();
        const heading = document.createElement('h3');
        const icon = document.createElement('span'); icon.className = 'section-icon';
        icon.setAttribute('aria-hidden', 'true');
        const title = match[1] || match[2];
        icon.textContent = /结论/.test(title) ? '✓' : /建议|下一步/.test(title) ? '→' : '≡';
        heading.appendChild(icon); heading.appendChild(document.createTextNode(title));
        section.appendChild(heading); rest = paragraph.slice(match[0].length);
      }
      if (!rest) continue;
      const block = document.createElement('div'); block.className = 'answer-paragraph';
      // Keep every list marker and every word, only add a visual container.
      const lines = rest.split('\n');
      lines.forEach((line, index) => {
        if (/^\s*(?:[-•–]|\d+[.)、])\s*/.test(line)){
          const row = document.createElement('div'); row.className = 'rule-line';
          inline(row, line); block.appendChild(row);
        } else inline(block, line);
        if (index < lines.length - 1) block.appendChild(document.createTextNode('\n'));
      });
      section.appendChild(block);
    }
    bubble.insertBefore(content, textNodes[0]);
    textNodes.forEach(node => node.remove());
  }
  const chat = document.getElementById('chat');
  if (!chat) return;
  function refresh(){
    const atBottom = chat.scrollHeight - chat.scrollTop - chat.clientHeight < 100;
    chat.querySelectorAll('.bot .bubble').forEach(format);
    if (atBottom) chat.scrollTop = chat.scrollHeight;
  }
  new MutationObserver(refresh).observe(chat, {childList:true, subtree:true, characterData:true});
  refresh();
})();
