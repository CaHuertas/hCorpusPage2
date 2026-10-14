// Resaltado de sintaxis mínimo para R y botón "Copiar" en los bloques de código.
// Sin dependencias: se aplica a <pre><code class="language-r"> dentro de .code-block.
(function () {
  "use strict";

  var KEYWORDS = /^(?:function|if|else|for|while|repeat|in|next|break|return|TRUE|FALSE|NULL|NA|NA_integer_|NA_real_|NA_character_|Inf|NaN)$/;

  // Orden importa: el primer grupo que coincide gana.
  var TOKEN = new RegExp([
    "(#[^\\n]*)",                                   // 1 comentario
    "(\"(?:[^\"\\\\]|\\\\.)*\"|'(?:[^'\\\\]|\\\\.)*')", // 2 texto
    "(`[^`]*`)",                                    // 3 nombre entre comillas invertidas
    "(\\b\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?L?\\b)", // 4 número
    "([A-Za-z.][A-Za-z0-9._]*)",                    // 5 identificador
    "(\\|>|<<-|->>|<-|->|%[^%\\n]*%|::|==|!=|<=|>=|&&|\\|\\||[~=+\\-*/^$@<>!&|:])" // 6 operador
  ].join("|"), "g");

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function wrap(cls, s) {
    return '<span class="tok-' + cls + '">' + esc(s) + "</span>";
  }

  function highlight(src) {
    var out = "";
    var last = 0;
    var m;
    TOKEN.lastIndex = 0;
    while ((m = TOKEN.exec(src)) !== null) {
      out += esc(src.slice(last, m.index));
      if (m[1]) out += wrap("c", m[1]);
      else if (m[2]) out += wrap("s", m[2]);
      else if (m[3]) out += esc(m[3]);
      else if (m[4]) out += wrap("n", m[4]);
      else if (m[5]) {
        var rest = src.slice(TOKEN.lastIndex);
        if (KEYWORDS.test(m[5])) out += wrap("k", m[5]);
        else if (/^\s*\(/.test(rest)) out += wrap("f", m[5]);
        else out += esc(m[5]);
      } else if (m[6]) out += wrap("o", m[6]);
      last = TOKEN.lastIndex;
    }
    return out + esc(src.slice(last));
  }

  document.querySelectorAll(".code-block").forEach(function (block) {
    var code = block.querySelector("code");
    if (!code) return;
    var raw = code.textContent;

    if (code.classList.contains("language-r")) {
      code.innerHTML = highlight(raw);
    }

    if (!navigator.clipboard) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "code-copy";
    btn.textContent = "Copiar";
    btn.setAttribute("aria-label", "Copiar el código");
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(raw).then(function () {
        btn.textContent = "Copiado";
        setTimeout(function () { btn.textContent = "Copiar"; }, 1800);
      });
    });
    block.appendChild(btn);
  });
})();
