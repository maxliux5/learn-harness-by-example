const chapters = [
  {
    id: "00-case-study",
    number: "00",
    title: "案例导读：一次失败暴露 Harness 的必要性",
    command: "python3 examples/ch00_case_study.py",
  },
  {
    id: "01-why-harness",
    number: "01",
    title: "为什么 Agent 需要 Harness",
    command: "python3 examples/ch01_why_harness.py",
  },
  {
    id: "02-minimal-loop",
    number: "02",
    title: "第一个最小 Agent Loop",
    command: "python3 examples/ch02_minimal_loop.py",
  },
  {
    id: "03-model-provider",
    number: "03",
    title: "把模型 Provider 抽象出来",
    command: "python3 examples/ch03_model_provider.py",
  },
  {
    id: "04-tools",
    number: "04",
    title: "给 Agent 增加工具",
    command: "python3 examples/ch04_tools.py",
  },
  {
    id: "05-run-state",
    number: "05",
    title: "管理一次运行的状态",
    command: "python3 examples/ch05_run_state.py",
  },
  {
    id: "06-trace-observability",
    number: "06",
    title: "加入 Trace 和可观测性",
    command: "python3 examples/ch06_trace_observability.py",
  },
  {
    id: "07-eval",
    number: "07",
    title: "从 Demo 走向 Eval",
    command: "python3 examples/ch07_eval.py",
  },
  {
    id: "08-failure-driven",
    number: "08",
    title: "失败案例驱动改进",
    command: "python3 examples/ch08_failure_driven.py",
  },
  {
    id: "09-replay-compare",
    number: "09",
    title: "回放、对比和版本化",
    command: "python3 examples/ch09_replay_compare.py",
  },
  {
    id: "10-final-project",
    number: "10",
    title: "整理成一个最小 Harness 项目",
    command: "python3 examples/ch10_research_harness.py",
  },
];

const nav = document.querySelector("#chapter-nav");
const article = document.querySelector("#article");
const toc = document.querySelector("#toc");
const runCommand = document.querySelector("#run-command");

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function slugify(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, "-")
    .replace(/^-+|-+$/g, "");
}

function inlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
}

function markdownToHtml(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let i = 0;
  let inCode = false;
  let codeLang = "";
  let codeLines = [];
  let inList = false;
  let inOrdered = false;
  let inTable = false;

  function closeList() {
    if (inList) {
      html.push(inOrdered ? "</ol>" : "</ul>");
      inList = false;
      inOrdered = false;
    }
  }

  function closeTable() {
    if (inTable) {
      html.push("</tbody></table>");
      inTable = false;
    }
  }

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("```")) {
      if (inCode) {
        html.push(`<pre><code class="language-${escapeHtml(codeLang)}">${escapeHtml(codeLines.join("\n"))}</code></pre>`);
        inCode = false;
        codeLang = "";
        codeLines = [];
      } else {
        closeList();
        closeTable();
        inCode = true;
        codeLang = line.slice(3).trim();
      }
      i += 1;
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      i += 1;
      continue;
    }

    if (!line.trim()) {
      closeList();
      closeTable();
      i += 1;
      continue;
    }

    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) {
      closeList();
      closeTable();
      const level = heading[1].length;
      const text = heading[2].trim();
      const id = slugify(text);
      html.push(`<h${level} id="${id}">${inlineMarkdown(text)}</h${level}>`);
      i += 1;
      continue;
    }

    if (line.startsWith("> ")) {
      closeList();
      closeTable();
      html.push(`<blockquote>${inlineMarkdown(line.slice(2))}</blockquote>`);
      i += 1;
      continue;
    }

    const unordered = /^[-*]\s+(.+)$/.exec(line);
    const ordered = /^\d+\.\s+(.+)$/.exec(line);
    if (unordered || ordered) {
      closeTable();
      const orderedNow = Boolean(ordered);
      if (!inList || inOrdered !== orderedNow) {
        closeList();
        html.push(orderedNow ? "<ol>" : "<ul>");
        inList = true;
        inOrdered = orderedNow;
      }
      html.push(`<li>${inlineMarkdown((unordered || ordered)[1])}</li>`);
      i += 1;
      continue;
    }

    if (line.includes("|") && lines[i + 1]?.match(/^\s*\|?\s*-+/)) {
      closeList();
      closeTable();
      const headers = line.split("|").map((cell) => cell.trim()).filter(Boolean);
      html.push("<table><thead><tr>");
      headers.forEach((header) => html.push(`<th>${inlineMarkdown(header)}</th>`));
      html.push("</tr></thead><tbody>");
      inTable = true;
      i += 2;
      continue;
    }

    if (inTable && line.includes("|")) {
      const cells = line.split("|").map((cell) => cell.trim()).filter(Boolean);
      html.push("<tr>");
      cells.forEach((cell) => html.push(`<td>${inlineMarkdown(cell)}</td>`));
      html.push("</tr>");
      i += 1;
      continue;
    }

    closeList();
    closeTable();
    html.push(`<p>${inlineMarkdown(line)}</p>`);
    i += 1;
  }

  closeList();
  closeTable();
  return html.join("\n");
}

function renderNav(currentId) {
  nav.innerHTML = chapters
    .map((chapter) => {
      const active = chapter.id === currentId ? " active" : "";
      return `
        <a class="chapter-link${active}" href="#/${chapter.id}">
          <span class="chapter-index">${chapter.number}</span>
          <span class="chapter-title">${chapter.title}</span>
        </a>
      `;
    })
    .join("");
}

function renderToc(current) {
  const headings = article.querySelectorAll("h2, h3");
  toc.innerHTML = Array.from(headings)
    .map((heading) => `<a href="#/${current.id}/${heading.id}">${heading.textContent}</a>`)
    .join("");
}

function renderFooter(current) {
  const index = chapters.findIndex((chapter) => chapter.id === current.id);
  const previous = chapters[index - 1];
  const next = chapters[index + 1];
  const footer = document.createElement("footer");
  footer.className = "chapter-footer";
  footer.innerHTML = `
    ${previous ? `<a href="#/${previous.id}">上一章：${previous.title}</a>` : "<span></span>"}
    ${next ? `<a href="#/${next.id}">下一章：${next.title}</a>` : "<span></span>"}
  `;
  article.appendChild(footer);
}

async function loadChapter() {
  const route = location.hash.replace(/^#\/?/, "");
  const [chapterId, targetHeading] = route.split("/");
  const current = chapters.find((chapter) => chapter.id === chapterId) || chapters[0];
  renderNav(current.id);
  runCommand.textContent = current.command;
  article.innerHTML = '<div class="loading">正在加载章节...</div>';

  try {
    const response = await fetch(`./chapters/${current.id}.md`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const markdown = await response.text();
    article.innerHTML = markdownToHtml(markdown);
    renderFooter(current);
    renderToc(current);
    const target = targetHeading ? document.getElementById(targetHeading) : null;
    if (target) {
      target.scrollIntoView({ behavior: "instant", block: "start" });
    } else {
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  } catch (error) {
    article.innerHTML = `<div class="error">章节加载失败：${escapeHtml(error.message)}</div>`;
    toc.innerHTML = "";
  }
}

window.addEventListener("hashchange", loadChapter);
loadChapter();
