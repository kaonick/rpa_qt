document.addEventListener('DOMContentLoaded', function () {
    // --- DOM Elements ---
    const naviBlock = document.getElementById('navi-block');
    const categoryListBlock = document.getElementById('category-list-block');
    const contentBlock = document.getElementById('content-block');
    const categoryToggleBtn = document.getElementById('category-toggle-btn');
    const categoryCollapsibleContent = document.getElementById('category-collapsible-content');
    const dynamicContent = document.getElementById('dynamic-content');
    const breadcrumb = document.getElementById('breadcrumb');

    // Popups and Buttons
    const popups = {
        info: { btn: document.getElementById('info-btn'), popup: document.getElementById('info-popup') },
        setting: { btn: document.getElementById('setting-btn'), popup: document.getElementById('setting-popup') },
        user: { btn: document.getElementById('user-btn'), popup: document.getElementById('user-popup') }
    };

    // Search
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');

    // Category List
    const categoryTabs = document.querySelectorAll('.category-tab-btn');
    const storeTree = document.getElementById('store-tree');
    const categoryTree = document.getElementById('category-tree');

    // --- Mock Data ---
    const mockNotifications = [
        { id: 1, text: '系統將於 03:00 AM 進行維護。', time: '5分鐘前' },
        { id: 2, text: '您的訂單 #1025 已出貨。', time: '1小時前' },
        { id: 3, text: '張經理分享了一份文件給您。', time: '3小時前' },
        { id: 4, text: '歡迎使用新版系統！', time: '1天前' }
    ];

    const mockStoreData = [
        { type: '飯店', stores: ['福華大飯店', '君悅酒店', '喜來登大飯店喜來登大飯店','福華大飯店', '君悅酒店', '喜來登大飯店','福華大飯店', '君悅酒店', '喜來登大飯店','福華大飯店', '君悅酒店', '喜來登大飯店'] },
        { type: '餐飲', stores: ['鼎泰豐', '王品牛排', '海底撈'] },
        { type: '零售', stores: ['新光三越', '遠東百貨', '誠品生活'] }
    ];

    const mockCategoryData = [
        { type: '電子產品', categories: ['手機', '筆記型電腦', '相機'] },
        { type: '居家生活', categories: ['廚具', '寢具', '清潔用品'] }
    ];

    // --- Functions ---

    // Close all popups
    function closeAllPopups() {
        Object.values(popups).forEach(p => p.popup.classList.add('hidden'));
    }

    // Update breadcrumb
    function updateBreadcrumb(pathArray) {
        breadcrumb.innerHTML = pathArray.map((item, index) => {
            if (index < pathArray.length - 1) {
                return `<span class="text-gray-500">${item}</span><span class="mx-2">/</span>`;
            }
            return `<span class="font-semibold text-gray-800">${item}</span>`;
        }).join('');
    }

    // Render content for a specific page
    function renderPage(type, pageName) {
        let path = [];
        let contentHTML = '';

        if (type === 'user' || type === 'setting') {
            path = ['作業', pageName];
            contentHTML = `<div class="p-8 bg-white rounded-lg shadow">
                <h2 class="text-2xl font-bold mb-4">${pageName}</h2>
                <p>這裡是「${pageName}」的設定頁面內容。</p>
                <!-- Add form elements or other content here -->
            </div>`;
        } else if (type === 'store') {
            path = ['資料', '店家', pageName];
            contentHTML = `<div class="p-8 bg-white rounded-lg shadow">
                <h2 class="text-2xl font-bold mb-4">${pageName} - 商品列表</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    ${Array(12).fill(0).map((_, i) => `
                        <div class="border rounded-lg p-4">
                            <div class="bg-gray-200 h-32 rounded mb-2"></div>
                            <h3 class="font-bold">商品 ${i + 1}</h3>
                            <p class="text-sm text-gray-600">商品描述文字...</p>
                            <p class="text-lg font-semibold text-blue-600 mt-2">$${Math.floor(Math.random() * 1000) + 100}</p>
                        </div>
                    `).join('')}
                </div>
            </div>`;
        } else if (type === 'search') {
             path = ['搜尋結果', `"${pageName}"`];
             contentHTML = `<div class="bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-bold mb-4">關於 "${pageName}" 的搜尋結果</h2>
                <div class="space-y-6">
                    ${Array(10).fill(0).map((_, i) => `
                        <div>
                            <a href="#" class="text-lg text-blue-700 hover:underline">搜尋結果標題 ${i + 1}</a>
                            <p class="text-sm text-green-700">https://example.com/result/${i+1}</p>
                            <p class="text-gray-600 mt-1">這是關於搜尋結果的簡短描述文字，幫助使用者快速了解內容摘要...</p>
                        </div>
                    `).join('')}
                </div>
                <div class="mt-8 flex justify-center items-center gap-2 text-sm">
                    <a href="#" class="px-3 py-1 border rounded hover:bg-gray-100">‹ 上一頁</a>
                    <a href="#" class="px-3 py-1 border rounded bg-blue-500 text-white">1</a>
                    <a href="#" class="px-3 py-1 border rounded hover:bg-gray-100">2</a>
                    <a href="#" class="px-3 py-1 border rounded hover:bg-gray-100">3</a>
                    <span>...</span>
                    <a href="#" class="px-3 py-1 border rounded hover:bg-gray-100">10</a>
                    <a href="#" class="px-3 py-1 border rounded hover:bg-gray-100">下一頁 ›</a>
                </div>
             </div>`;
        }

        dynamicContent.innerHTML = contentHTML;
        updateBreadcrumb(path);
    }

    // --- Event Listeners ---

    // Popup toggles
    Object.keys(popups).forEach(key => {
        popups[key].btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = popups[key].popup.classList.contains('hidden');
            closeAllPopups();
            if (isHidden) {
                popups[key].popup.classList.remove('hidden');
            }
        });
    });

    // Global click to close popups
    document.addEventListener('click', () => {
        closeAllPopups();
    });

    // Prevent popups from closing when clicked inside
    Object.values(popups).forEach(p => {
        p.popup.addEventListener('click', e => e.stopPropagation());
    });

    // Category list toggle
    categoryToggleBtn.addEventListener('click', () => {
        categoryListBlock.classList.toggle('w-3/10');
        categoryListBlock.classList.toggle('w-0');

        contentBlock.classList.toggle('w-7/10');
        contentBlock.classList.toggle('w-full');

        categoryCollapsibleContent.classList.toggle('opacity-0');
        categoryCollapsibleContent.classList.toggle('pointer-events-none');
    });

    // Search form submission
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) {
            renderPage('search', query);
            searchInput.value = '';
        }
    });

    // Setting and User menu items
    document.querySelectorAll('.setting-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            renderPage('setting', e.currentTarget.dataset.page);
            closeAllPopups();
        });
    });
    document.querySelectorAll('.user-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            renderPage('user', e.currentTarget.dataset.page);
            closeAllPopups();
        });
    });

    // Category tabs
    categoryTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            categoryTabs.forEach(t => {
                t.classList.remove('text-blue-600', 'border-blue-600');
                t.classList.add('text-gray-500');
            });
            e.currentTarget.classList.add('text-blue-600', 'border-blue-600');
            e.currentTarget.classList.remove('text-gray-500');

            document.getElementById('store-tree').classList.add('hidden');
            document.getElementById('category-tree').classList.add('hidden');
            document.getElementById(e.currentTarget.dataset.target).classList.remove('hidden');
        });
    });

    // Tree view interaction
    function setupTreeListeners(treeElement) {
        treeElement.addEventListener('click', (e) => {
            const target = e.target;
            // Handle expand/collapse
            if (target.matches('.tree-item-toggle, .tree-item-toggle *')) {
                const parentLi = target.closest('li');
                const sublist = parentLi.querySelector('ul');
                const icon = parentLi.querySelector('.toggle-icon');
                if (sublist) {
                    sublist.classList.toggle('hidden');
                    icon.classList.toggle('rotate-90');
                }
            }
            // Handle item selection
            else if (target.matches('.tree-leaf-item')) {
                renderPage('store', target.textContent.trim());
            }
        });
    }

    // --- Initial Population ---

    // Populate notifications
    const notificationList = document.getElementById('notification-list');
    notificationList.innerHTML = mockNotifications.map(n => `
        <li class="notification-item flex items-start gap-3 p-3 hover:bg-gray-100">
            <div class="flex-grow">
                <p class="text-sm text-gray-800">${n.text}</p>
                <p class="text-xs text-gray-500 mt-1">${n.time}</p>
            </div>
            <button class="mark-as-read p-1 text-gray-400 hover:text-red-500">
                <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
            </button>
        </li>
    `).join('');
    notificationList.addEventListener('click', (e) => {
        if (e.target.closest('.mark-as-read')) {
            e.target.closest('.notification-item').style.display = 'none';
        }
    });

    // Populate store tree
    storeTree.innerHTML = mockStoreData.map(group => `
        <li>
            <div class="tree-item-toggle flex items-center justify-between p-2 rounded hover:bg-gray-100 cursor-pointer">
                <span class="font-semibold text-gray-700">${group.type}</span>
                <svg class="toggle-icon w-4 h-4 text-gray-500 transition-transform" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
            </div>
            <ul class="hidden pl-4 mt-1 space-y-1 border-l ml-2">
                ${group.stores.map(store => `
                    <li><a href="#" class="tree-leaf-item block p-2 rounded text-gray-600 hover:bg-blue-50 hover:text-blue-600">${store}</a></li>
                `).join('')}
            </ul>
        </li>
    `).join('');

    // Populate category tree
    categoryTree.innerHTML = mockCategoryData.map(group => `
        <li>
            <div class="tree-item-toggle flex items-center justify-between p-2 rounded hover:bg-gray-100 cursor-pointer">
                <span class="font-semibold text-gray-700">${group.type}</span>
                <svg class="toggle-icon w-4 h-4 text-gray-500 transition-transform" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
            </div>
            <ul class="hidden pl-4 mt-1 space-y-1 border-l ml-2">
                ${group.categories.map(cat => `
                    <li><a href="#" class="tree-leaf-item block p-2 rounded text-gray-600 hover:bg-blue-50 hover:text-blue-600">${cat}</a></li>
                `).join('')}
            </ul>
        </li>
    `).join('');

    setupTreeListeners(storeTree);
    setupTreeListeners(categoryTree);
});





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
