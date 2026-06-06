// Demo 站点应用逻辑 - 用于测试代码覆盖

function greet(name) {
  return `欢迎回来,${name}`;
}

function validateLogin(username, password) {
  if (!username || !password) {
    return false;
  }
  if (password.length < 6) {
    return false;
  }
  return true;
}

function handleLogin(event) {
  event.preventDefault();
  const username = document.getElementById('user').value;
  const password = document.getElementById('pwd').value;

  if (validateLogin(username, password)) {
    // 模拟登录成功
    window.location.href = 'dashboard.html';
  } else {
    alert('登录失败：用户名或密码错误');
  }
}

// 页面加载时绑定事件
document.addEventListener('DOMContentLoaded', function() {
  const loginForm = document.getElementById('login');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
});

// 导出函数供测试
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { greet, validateLogin };
}