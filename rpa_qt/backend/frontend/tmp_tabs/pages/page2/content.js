let callback;

export function init(params, sendBack) {
  callback = sendBack;
  document.getElementById("welcome").textContent = `你好，${params.name}！`;
}

window.sendBack = function () {
  if (callback) callback({ message: "從 Page1 回傳的資料" });
};
