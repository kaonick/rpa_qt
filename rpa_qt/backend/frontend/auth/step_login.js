document.addEventListener('DOMContentLoaded', () => {
    const steps = {
        1: document.getElementById('step-1'),
        2: document.getElementById('step-2'),
        3: document.getElementById('step-3'),
        4: document.getElementById('step-4')
    };

    let currentStep = 1;
    const state = {
        loginId: '',
        isEmail: false,
        isPhone: false
    };

    function showStep(stepNumber) {
        Object.values(steps).forEach(step => step.classList.remove('active'));
        steps[stepNumber].classList.add('active');
        currentStep = stepNumber;
    }

    // 清除錯誤訊息
    function clearErrors() {
        document.querySelectorAll('.error-message').forEach(el => el.style.display = 'none');
    }

    // 模擬後端 API 呼叫
    async function mockApiCall(endpoint, data) {
        console.log(`Mock API Call to ${endpoint}`, data);
        // 模擬延遲
        await new Promise(resolve => setTimeout(resolve, 1000));
        return { success: true, message: '操作成功' };
    }

    // --- 第四步：跳轉主頁 ---
    function goToMainPage() {
        showStep(4);
        setTimeout(() => {
            // 實際應替換為你的主頁網址
            window.location.href = 'https://example.com/main';
        }, 2000);
    }

    // --- 第一步邏輯 ---
    document.getElementById('next-step-1').addEventListener('click', async () => {
        clearErrors();
        const loginId = document.getElementById('login-id').value.trim();
        const errorElement = document.getElementById('login-id-error');

        if (!loginId) {
            errorElement.textContent = '請輸入電子郵件或手機號碼';
            errorElement.style.display = 'block';
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const phoneRegex = /^09\d{8}$/;

        if (emailRegex.test(loginId)) {
            state.loginId = loginId;
            state.isEmail = true;
            state.isPhone = false;
            showStep(2);
        } else if (phoneRegex.test(loginId)) {
            state.loginId = loginId;
            state.isEmail = false;
            state.isPhone = true;
            showStep(2);
        } else {
            errorElement.textContent = '格式不正確，請輸入有效的電子郵件或手機號碼';
            errorElement.style.display = 'block';
        }
    });

    // --- OAuth 登入邏輯 ---
    document.querySelectorAll('.oauth-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const provider = e.currentTarget.dataset.provider;
            console.log(`正在使用 ${provider} 進行 OAuth 登入...`);

            // 模擬後端 OAuth 呼叫
            const response = await mockApiCall('/api/oauth/login', { provider });

            if (response.success) {
                // 模擬 OAuth 登入成功，直接跳轉到主頁
                goToMainPage();
            } else {
                alert('OAuth 登入失敗，請稍後再試。');
            }
        });
    });

    // --- 第二步邏輯 ---
    document.getElementById('next-step-2').addEventListener('click', async () => {
        clearErrors();
        const password = document.getElementById('password').value.trim();
        const errorElement = document.getElementById('password-error');

        if (!password) {
            errorElement.textContent = '請輸入密碼';
            errorElement.style.display = 'block';
            return;
        }

        // 模擬後端登入 API 呼叫
        const response = await mockApiCall('/api/login', {
            loginId: state.loginId,
            password: password
        });

        if (response.success) {
            // 後端發送驗證碼成功
            document.getElementById('verification-target').textContent = state.loginId;
            showStep(3);
        } else {
            // 處理登入失敗，例如密碼錯誤
            errorElement.textContent = '帳號或密碼錯誤';
            errorElement.style.display = 'block';
        }
    });

    // --- 第三步邏輯 ---
    document.getElementById('submit-btn').addEventListener('click', async () => {
        clearErrors();
        const verificationCode = document.getElementById('verification-code').value.trim();
        const errorElement = document.getElementById('verification-code-error');

        if (!verificationCode) {
            errorElement.textContent = '請輸入驗證碼';
            errorElement.style.display = 'block';
            return;
        }

        // 模擬後端驗證碼 API 呼叫
        const response = await mockApiCall('/api/verify', {
            loginId: state.loginId,
            code: verificationCode
        });

        if (response.success) {
            // 驗證碼符合，登入成功
            goToMainPage();
        } else {
            errorElement.textContent = '驗證碼錯誤或已過期';
            errorElement.style.display = 'block';
        }
    });

    // --- 返回上一步連結 ---
    document.querySelectorAll('.back-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetStep = parseInt(e.currentTarget.dataset.step);
            showStep(targetStep);
        });
    });
});