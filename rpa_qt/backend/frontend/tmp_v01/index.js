function loadPage(page, params = {}) {
  fetch(`pages/${page}.html`)
    .then(res => res.text())
    .then(html => {
      const container = document.getElementById("content-block");

      // 清掉原有子頁的樣式與內容
      container.innerHTML = "";
      document.querySelectorAll("[data-sub-style]").forEach(el => el.remove());

      // 解析 HTML 並抽取 <style> 或 <link>
      const temp = document.createElement("div");
      temp.innerHTML = html;

      // 將 style/link 加到 <head>
      temp.querySelectorAll("style, link[rel='stylesheet']").forEach(el => {
        el.dataset.subStyle = "true";  // 標記為子頁樣式
        document.head.appendChild(el.cloneNode(true));
      });

      // 將其餘內容塞入 content 區塊
      temp.querySelectorAll(":not(style):not(link)").forEach(el => {
        container.appendChild(el);
      });

      // 載入 JS
      const script = document.createElement("script");
      script.src = `js/${page}.js`;
      script.dataset.dynamic = "true";
      // 當 script 載入完成後，呼叫初始化函數並傳入參數
      script.onload = () => {
        if (typeof window[`init_${page}`] === 'function') {
          window[`init_${page}`](params);
        }
      };
      document.body.appendChild(script);
    })
    .catch(err => {
      console.error(err);
      document.getElementById("content-block").innerHTML = "<p>無法載入子頁內容</p>";
    });
}
