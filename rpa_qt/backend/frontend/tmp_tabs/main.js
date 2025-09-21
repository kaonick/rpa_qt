const maxTabs = 10;
const tabs = new Map(); // id => { container, params }

function openPageTab(id, params = {}) {
  if (tabs.size >= maxTabs && !tabs.has(id)) {
    alert("最多只能開啟 10 個子頁！");
    return;
  }

  if (!tabs.has(id)) {
    const tabBar = document.getElementById("tab-bar");
    const tabContent = document.getElementById("tab-content");

    // 建立 tab header
    const tab = document.createElement("div");
    tab.className = "tab";
    tab.innerHTML = `<span class="tab-title">${id}<span class="close" onclick="closeTab(event, '${id}')">✕</span>`;
    tab.onclick = () => activateTab(id);
    tabBar.appendChild(tab);

    // 建立內容區塊
    const container = document.createElement("div");
    container.className = "tab-pane";
    container.id = `tab-${id}`;
    tabContent.appendChild(container);

    // 載入 HTML、CSS、JS
    loadPage(id, container, params);

    tabs.set(id, { tab, container, params });
  }

  activateTab(id);
}

function closeTab(e, id) {
  e.stopPropagation();

  const entry = tabs.get(id);
  if (entry) {
    entry.tab.remove();
    entry.container.remove();
    tabs.delete(id);
  }

  // 切換到其他頁
  const first = tabs.keys().next();
  if (!first.done) activateTab(first.value);
}

function activateTab(id) {
  for (const [key, { tab, container }] of tabs) {
    tab.classList.toggle("active", key === id);
    container.classList.toggle("active", key === id);
  }
}

async function loadPage(id, container, params) {
  const base = `pages/${id}/`;

  // 載入 HTML
  const html = await fetch(`${base}content.html`).then(res => res.text());
  container.innerHTML = html;

  // 載入 CSS
  const cssId = `css-${id}`;
  if (!document.getElementById(cssId)) {
    const link = document.createElement("link");
    link.id = cssId;
    link.rel = "stylesheet";
    link.href = `${base}content.css`;
    document.head.appendChild(link);
  }

  // 載入 JS 並傳入參數
  const js = await import(`./${base}content.js?${Date.now()}`);
  if (js.init) {
    js.init(params, (data) => {
      console.log(`[${id}] 回傳資料:`, data);
    });
  }
}
