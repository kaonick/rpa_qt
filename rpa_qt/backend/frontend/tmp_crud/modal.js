// DataModal 物件的完整程式碼
const DataModal = (function() {
    // ... (所有 DataModal 的程式碼，包括變數、函式和回傳物件) ...
    const modal = document.getElementById('dataModal');
    const modalContainer = document.getElementById('modalContainer');
    //console.log('modalContainer:', modalContainer);
    const modalTitle = document.getElementById('modalTitle');
    const modalSearchInput = document.getElementById('modalSearchInput');
    const modalSearchBtn = document.getElementById('modalSearchBtn');
    const modalTableHead = document.getElementById('modalTableHead');
    const modalTableBody = document.getElementById('modalTableBody');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const modalSelectBtn = document.getElementById('modalSelectBtn');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfo = document.getElementById('pageInfo');

    let currentOptions = {};
    let currentData = [];
    let currentPage = 1;
    let totalItems = 0;
    let sortedColumn = null;
    let sortDirection = 'asc';
    let selectedItems = new Set();

    const defaultOptions = {
        title: '選擇資料',
        apiEndpoint: '',
        columns: [],
        callback: () => {},
        multiSelect: false,
        modalWidth: 'sm:max-w-xl',
        modalHeight: '',
        pageSize: 10
    };

    function updateModalStyle(options) {
        alert('updateModalStyle！');



        modal.classList.remove("hidden"); // show modal

        //modalContainer.className = 'relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:w-full ' + options.modalWidth + (options.modalHeight ? ' ' + options.modalHeight : '');
        //modal.style.display = 'block';
    }

    //function updateModalStyle(options) {
        //modalContainer.className = `relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:w-full ${options.modalWidth} ${options.modalHeight}`;
        //modal.classList.remove('hidden');
        //modal.style.display = 'block'; // This is no longer necessary but doesn't hurt.
    //}

    async function fetchData(searchQuery, page, sortKey, sortDir) {
        const { apiEndpoint, columns } = currentOptions;
        if (!apiEndpoint || !columns.length) return;

        try {
            const queryParams = new URLSearchParams();
            if (searchQuery) queryParams.append('search', searchQuery);
            if (page) queryParams.append('page', page);
            if (sortKey) {
                queryParams.append('sort_by', sortKey);
                queryParams.append('sort_dir', sortDir);
            }
            // 這裡假設後端API支援分頁和排序參數
            const response = await fetch(`${apiEndpoint}?${queryParams.toString()}`);
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            // 假設後端回傳格式為 { items: [], total_items: 100 }
            currentData = data.items || data;
            totalItems = data.total_items || currentData.length;
            renderTable();
            updatePagination();

        } catch (error) {
            console.error('Fetch error:', error);
            modalTableBody.innerHTML = '<tr><td colspan="100" class="p-4 text-center text-red-500">無法載入資料，請檢查後端服務。</td></tr>';
        }
    }

    function renderTable() {
        const { columns, multiSelect } = currentOptions;
        modalTableHead.innerHTML = '';
        modalTableBody.innerHTML = '';

        // 渲染表頭
        const headerRow = document.createElement('tr');
        if (multiSelect) {
            headerRow.innerHTML += `<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-10">
                <input type="checkbox" id="selectAllCheckbox" class="rounded text-blue-600 focus:ring-blue-500">
            </th>`;
        }
        columns.forEach(col => {
            const header = document.createElement('th');
            header.className = 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer';
            header.textContent = col.title;
            if (col.sortable) {
                header.innerHTML += ` <span class="sort-icon">${sortedColumn === col.key ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>`;
                header.addEventListener('click', () => handleSort(col.key));
            }
            headerRow.appendChild(header);
        });
        modalTableHead.appendChild(headerRow);

        // 渲染資料
        currentData.forEach(item => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-100 transition-colors duration-150';

            if (multiSelect) {
                const isSelected = selectedItems.has(item.id); // 假設有id
                row.innerHTML += `<td class="px-6 py-4 whitespace-nowrap w-10">
                    <input type="checkbox" class="row-checkbox rounded text-blue-600 focus:ring-blue-500" data-id="${item.id}" ${isSelected ? 'checked' : ''}>
                </td>`;
            }

            columns.forEach(col => {
                const cell = document.createElement('td');
                cell.className = 'px-6 py-4 whitespace-nowrap text-sm text-gray-900';
                cell.textContent = item[col.key] || '';
                row.appendChild(cell);
            });

            row.addEventListener('click', (e) => {
                if (multiSelect) {
                    const checkbox = row.querySelector('.row-checkbox');
                    checkbox.checked = !checkbox.checked;
                    handleSelection(checkbox.checked, item);
                } else {
                    currentOptions.callback([item]);
                    closeModal();
                }
            });
            modalTableBody.appendChild(row);
        });

        if (multiSelect) {
            const selectAllCheckbox = document.getElementById('selectAllCheckbox');
            selectAllCheckbox.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                document.querySelectorAll('.row-checkbox').forEach(checkbox => {
                    checkbox.checked = isChecked;
                    handleSelection(isChecked, currentData.find(d => d.id == checkbox.dataset.id));
                });
            });
        }
    }

    function updatePagination() {
        const { pageSize } = currentOptions;
        const totalPages = Math.ceil(totalItems / pageSize);
        pageInfo.textContent = `第 ${currentPage} / ${totalPages} 頁`;
        prevPageBtn.disabled = currentPage <= 1;
        nextPageBtn.disabled = currentPage >= totalPages;
    }

    function handleSearch() {
        currentPage = 1;
        fetchData(modalSearchInput.value.trim(), currentPage);
    }

    function handleSort(columnKey) {
        if (sortedColumn === columnKey) {
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            sortedColumn = columnKey;
            sortDirection = 'asc';
        }
        currentPage = 1;
        fetchData(modalSearchInput.value.trim(), currentPage, sortedColumn, sortDirection);
    }

    function handleSelection(isChecked, item) {
        if (isChecked) {
            selectedItems.add(item);
        } else {
            selectedItems.delete(item);
        }
        modalSelectBtn.classList.toggle('hidden', selectedItems.size === 0);
    }

    function openModal(options) {
        console.log('Opening modal with options:', options);
        currentOptions = { ...defaultOptions, ...options };
        modalTitle.textContent = currentOptions.title;
        updateModalStyle(currentOptions);

        selectedItems.clear();
        modalSelectBtn.classList.add('hidden');
        modalSearchInput.value = '';
        currentPage = 1;
        sortedColumn = null;
        sortDirection = 'asc';

        // 重新綁定事件，防止重複
        modalSearchBtn.onclick = handleSearch;
        prevPageBtn.onclick = () => {
            if (currentPage > 1) {
                currentPage--;
                fetchData(modalSearchInput.value.trim(), currentPage, sortedColumn, sortDirection);
            }
        };
        nextPageBtn.onclick = () => {
            const totalPages = Math.ceil(totalItems / currentOptions.pageSize);
            if (currentPage < totalPages) {
                currentPage++;
                fetchData(modalSearchInput.value.trim(), currentPage, sortedColumn, sortDirection);
            }
        };
        modalCloseBtn.onclick = closeModal;
        modalSelectBtn.onclick = () => {
            currentOptions.callback([...selectedItems]);
            closeModal();
        };

        fetchData('', currentPage);
    }

    function closeModal() {
        modal.classList.add("hidden"); // hide modal
        //modal.style.display = 'none';
        selectedItems.clear();
        document.body.style.overflow = '';
    }

    // 外部API
    return {
        open: openModal,
        close: closeModal
    };
})();