//接收傳入參數
window.init_profile = function(params) {
  const { userId } = params;
  document.getElementById("profile-info").innerText = `載入使用者 ${userId} 的資料`;
  // 你可以在這裡用 fetch 請求 API 等等
};


// 以下這段似乎無作用。
document.addEventListener("DOMContentLoaded", () => {
  const profileDiv = document.getElementById("profile-info");
  if (profileDiv) {
    profileDiv.innerText = "載入個人資料成功！";
  }
});
