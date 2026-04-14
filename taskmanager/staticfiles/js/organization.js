// =========================================
// СКРИПТЫ ДЛЯ СТРАНИЦЫ ОРГАНИЗАЦИОННОЙ СТРУКТУРЫ
// =========================================

// Состояние дерева
const OrgTree = {
    expandedNodes: new Set(),
    
    // Переключить узел
    toggleNode: (nodeId, element) => {
        const treeNode = element.closest('.tree-node');
        const childrenContainer = document.getElementById(`children-${nodeId}`);
        const employeeContainer = document.getElementById(`employees-${nodeId}`);
        const toggleIcon = element.querySelector('.node-toggle i');
        
        // If no children or employees, return
        if (!childrenContainer && !employeeContainer) return;
        
        if (OrgTree.expandedNodes.has(nodeId)) {
            // Сворачиваем
            if (childrenContainer) childrenContainer.style.display = 'none';
            if (employeeContainer) employeeContainer.style.display = 'none';
            if (toggleIcon) {
                toggleIcon.className = 'bi bi-chevron-down';
                element.querySelector('.node-toggle').classList.remove('open');
            }
            OrgTree.expandedNodes.delete(nodeId);
        } else {
            // Разворачиваем
            if (childrenContainer) childrenContainer.style.display = 'flex';
            if (employeeContainer) employeeContainer.style.display = 'block';
            if (toggleIcon) {
                toggleIcon.className = 'bi bi-chevron-up';
                element.querySelector('.node-toggle').classList.add('open');
            }
            OrgTree.expandedNodes.add(nodeId);
        }
    },
    
    // Развернуть все
    expandAll: () => {
        document.querySelectorAll('.children-container').forEach(container => {
            container.style.display = 'flex';
        });
        document.querySelectorAll('.employee-list-container').forEach(container => {
            container.style.display = 'block';
        });
        document.querySelectorAll('.node-toggle i').forEach(icon => {
            icon.className = 'bi bi-chevron-up';
        });
        document.querySelectorAll('.node-toggle').forEach(toggle => {
            toggle.classList.add('open');
        });
        // Добавляем все узлы с детьми в expandedNodes
        document.querySelectorAll('.tree-node[data-id]').forEach(node => {
            const nodeId = node.getAttribute('data-id');
            const childrenContainer = document.getElementById(`children-${nodeId}`);
            const employeeContainer = document.getElementById(`employees-${nodeId}`);
            if (childrenContainer || employeeContainer) {
                OrgTree.expandedNodes.add(nodeId);
            }
        });
    },
    
    // Свернуть все
    collapseAll: () => {
        document.querySelectorAll('.children-container').forEach(container => {
            container.style.display = 'none';
        });
        document.querySelectorAll('.employee-list-container').forEach(container => {
            container.style.display = 'none';
        });
        document.querySelectorAll('.node-toggle i').forEach(icon => {
            icon.className = 'bi bi-chevron-down';
        });
        document.querySelectorAll('.node-toggle').forEach(toggle => {
            toggle.classList.remove('open');
        });
        OrgTree.expandedNodes.clear();
    }
};


// Управление сотрудниками
const Staff = {
    // Показать сотрудников отдела
    showDepartmentStaff: (deptId) => {
        const staffList = DomUtils.get(`dept-${deptId}-staff`);
        if (staffList) {
            DomUtils.toggle(staffList);
        }
    },
    
    // Показать сотрудников лаборатории
    showLabStaff: (labId) => {
        const staffList = DomUtils.get(`lab-${labId}-staff`);
        if (staffList) {
            DomUtils.toggle(staffList);
        }
    }
};

// Поиск по структуре
const Search = {
    searchInput: null,
    
    init: () => {
        Search.searchInput = DomUtils.get('search-input');
        if (Search.searchInput) {
            Search.searchInput.addEventListener('keyup', Search.performSearch);
        }
    },
    
    performSearch: (e) => {
        const term = e.target.value.toLowerCase();
        
        if (term.length < 2) {
            // Если меньше 2 символов, показываем всё
            DomUtils.queryAll('.tree-node').forEach(node => {
                node.style.display = 'flex';
            });
            return;
        }
        
        // Ищем по названиям
        DomUtils.queryAll('.tree-node').forEach(node => {
            const name = node.querySelector('.node-name')?.textContent.toLowerCase() || '';
            if (name.includes(term)) {
                node.style.display = 'flex';
                // Показываем родителей
                let parent = node.parentElement.closest('.tree-node');
                while (parent) {
                    parent.style.display = 'flex';
                    parent = parent.parentElement.closest('.tree-node');
                }
            } else {
                node.style.display = 'none';
            }
        });
    },
    
    clear: () => {
        if (Search.searchInput) {
            Search.searchInput.value = '';
            DomUtils.queryAll('.tree-node').forEach(node => {
                node.style.display = 'flex';
            });
        }
    }
};

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    console.log('Organization.js loaded');
    
    // Инициализируем поиск
    Search.init();
    
    // Скрываем все дочерние контейнеры и списки сотрудников по умолчанию
    document.querySelectorAll('.children-container').forEach(container => {
        container.style.display = 'none';
    });
    document.querySelectorAll('.employee-list-container').forEach(container => {
        container.style.display = 'none';
    });
});

// Экспортируем глобальные объекты
window.OrgTree = OrgTree;
window.Staff = Staff;
window.Search = Search;