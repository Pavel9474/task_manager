// =========================================
// ОСНОВНЫЕ ФУНКЦИИ ДЛЯ ВСЕГО ПРОЕКТА
// =========================================

// Утилиты для работы с DOM
const DomUtils = {
    // Получить элемент по ID
    get: (id) => document.getElementById(id),
    
    // Получить элементы по селектору
    query: (selector) => document.querySelector(selector),
    queryAll: (selector) => document.querySelectorAll(selector),
    
    // Добавить/удалить класс
    addClass: (element, className) => element.classList.add(className),
    removeClass: (element, className) => element.classList.remove(className),
    toggleClass: (element, className) => element.classList.toggle(className),
    
    // Показать/скрыть элемент
    show: (element) => element.style.display = 'block',
    hide: (element) => element.style.display = 'none',
    toggle: (element) => {
        if (element.style.display === 'none') {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    }
};

// Утилиты для работы с датами
const DateUtils = {
    // Форматировать дату
    format: (date, format = 'dd.mm.yyyy') => {
        const d = new Date(date);
        const day = d.getDate().toString().padStart(2, '0');
        const month = (d.getMonth() + 1).toString().padStart(2, '0');
        const year = d.getFullYear();
        
        return format
            .replace('dd', day)
            .replace('mm', month)
            .replace('yyyy', year);
    },
    
    // Получить разницу в днях
    diffDays: (date1, date2) => {
        const d1 = new Date(date1);
        const d2 = new Date(date2);
        const diffTime = Math.abs(d2 - d1);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    },
    
    // Проверить, просрочена ли дата
    isOverdue: (date) => {
        return new Date(date) < new Date();
    }
};

// Утилиты для уведомлений
const Notify = {
    // Показать сообщение
    show: (message, type = 'info', duration = 3000) => {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} fade-in`;
        alert.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : 
                                 type === 'danger' ? 'exclamation-circle' :
                                 type === 'warning' ? 'exclamation-triangle' :
                                 'info-circle'}"></i>
            ${message}
        `;
        
        const container = DomUtils.query('.alerts-container') || document.body;
        container.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, duration);
    },
    
    success: (message) => Notify.show(message, 'success'),
    error: (message) => Notify.show(message, 'danger'),
    warning: (message) => Notify.show(message, 'warning'),
    info: (message) => Notify.show(message, 'info')
};

// Утилиты для AJAX запросов
const Ajax = {
    // GET запрос
    get: async (url) => {
        try {
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('GET error:', error);
            Notify.error('Ошибка при загрузке данных');
        }
    },
    
    // POST запрос
    post: async (url, data) => {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('POST error:', error);
            Notify.error('Ошибка при отправке данных');
        }
    },
    
    // POST с FormData
    postForm: async (url, formData) => {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error('POST Form error:', error);
            Notify.error('Ошибка при отправке формы');
        }
    }
};

// Получить CSRF токен из cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('Main.js loaded');
    
    // Добавляем контейнер для уведомлений
    const alertsContainer = document.createElement('div');
    alertsContainer.className = 'alerts-container';
    alertsContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
    `;
    document.body.appendChild(alertsContainer);
});

// Экспортируем глобальные объекты
window.DomUtils = DomUtils;
window.DateUtils = DateUtils;
window.Notify = Notify;
window.Ajax = Ajax;