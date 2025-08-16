// 检查服务器状态
function checkServerStatus() {
    const statusElement = document.getElementById('status-message');
    statusElement.textContent = '正在检查服务器状态...';
    statusElement.className = 'status-message';
    
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            statusElement.textContent = `服务器状态: ${data.message}`;
            statusElement.className = 'status-message success';
        })
        .catch(error => {
            statusElement.textContent = '服务器连接失败';
            statusElement.className = 'status-message error';
            console.error('Error:', error);
        });
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('希望杀游戏页面已加载');
});
