
# prompt:生成CRUD網頁

```text
幫我寫一個資料表格的CRUD，用tailwindcss，只能用一般的html,js,css。
這個表格的後端是fastapi，提供crud的api供調用。
請以product為例，生成一個前端網頁。
網頁有左側應該是一個table list，可以依照搜尋條件，列出相關資料。
在table list中click任一筆，就會在右側顯示該筆的內容，右側採用form方式呈現。
使用者可以針對資料進行查詢、新增、修改、刪除等動作。
```


# prompt:生成modal視窗

```text
請參考以下的tailwindcss風格，用js動態生成一個modal視窗，這個model主要用來查找資料供選取後帶入form的資料中。
主要的功能包括：
1. modal視窗可以開啟與關閉。
2. modal視窗中有一個搜尋列，可以輸入關鍵字進行搜尋。
3. modal視窗中有一個table list，可以依照搜尋條件，列出相關資料。
4. 在table list中click任一筆，就會將該筆資料帶入form中，並關閉modal視窗。
5. modal視窗的table list支援分頁功能，每頁顯示10筆資料。
6. modal視窗的table list支援排序功能，可以依照欄位進行排序。
7. modal視窗的table list支援多選功能，可以選取多筆資料，並將選取的資料帶入form中，並關閉modal視窗。(此功能是可選的，可選擇多選或單選)。
8. modal的資料來源是透過fetch api從後端取得資料，可依照設定的資料表與欄位，還有查詢條件進行查詢。
9. modal視窗的樣式請參考以下的tailwindcss風格，並且可以自訂寬度與高度。
10. modal視窗的開啟與關閉，可以用js控制，也可以用tailwindcss的class來控制。
11. table list若超過頁面寬度與高度，請支援水平與垂直捲軸。

tailwindcss風格參考：
```html
<div class="flex-grow overflow-y-auto">
    <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50 sticky top-0">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">產品名稱</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">價格</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">庫存</th>
            </tr>
        </thead>
        <tbody id="productTableBody" class="bg-white divide-y divide-gray-200 cursor-pointer">
            </tbody>
    </table>
</div>

```
```
# modal的用引步驟：

1. 設定開啟modal的按鈕，並指定modal的id。
```html
<button type="button" id="openProductModalBtn" class="ml-2 bg-purple-500 text-white p-2 rounded-md hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-500">選擇產品</button>
<button id="openModalBtn" class="bg-blue-500 text-white px-4 py-2 rounded" onclick="openModal('myModal')">開啟Modal</button>
```
2. 在html中加入modal的div，並指定id。
```html
    <div id="modalBlock"></div>
```

3. 在js中加入動態載入modal.html與modal.js的程式碼。
```javascript
// 動態載入modal.html與modal.js

fetch('modal.html')
    .then(response => response.text())
    .then(html => {
        document.getElementById('modalBlock').innerHTML = html;

        // 載入 modal.js
        const script = document.createElement('script');
        script.src = 'modal.js';
        document.body.appendChild(script);
    })
    .catch(error => console.error('Error loading modal:', error));
```
4. 在modal.js中加入modal的功能程式碼。
```javascript
        const openProductModalBtn = document.getElementById('openProductModalBtn');

        openProductModalBtn.addEventListener('click', () => {
            DataModal.open({
                title: '選擇產品',
                apiEndpoint: 'http://127.0.0.1:8000/api/products',
                columns: [
                    { key: 'id', title: 'ID', sortable: true },
                    { key: 'name', title: '產品名稱', sortable: true },
                    { key: 'price', title: '價格', sortable: true },
                    { key: 'stock', title: '庫存', sortable: true }
                ],
                callback: (selectedProducts) => {
                    if (selectedProducts.length > 0) {
                        const product = selectedProducts[0];
                        document.getElementById('productId').value = product.id;
                        document.getElementById('name').value = product.name;
                        document.getElementById('price').value = product.price;
                        document.getElementById('stock').value = product.stock;
                        document.getElementById('description').value = product.description;
                    }
                },
                multiSelect: false,
                modalWidth: 'sm:max-w-4xl',
                pageSize: 10
            });
        });
```

