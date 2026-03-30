// =========================================
// СКРИПТЫ ДЛЯ СТРАНИЦЫ ОРГАНИЗАЦИОННОЙ СТРУКТУРЫ
// =========================================

// Состояние дерева
const OrgTree = {
    expandedNodes: new Set(),
    
    // Переключить узел
    toggleNode: (nodeId, element) => {
        const childrenContainer = DomUtils.get(`children-${nodeId}`);
        const icon = element.querySelector('.toggle-icon i');
        
        if (!childrenContainer) return;
        
        if (OrgTree.expandedNodes.has(nodeId)) {
            // Сворачиваем
            childrenContainer.style.display = 'none';
            if (icon) icon.className = 'bi bi-chevron-down';
            OrgTree.expandedNodes.delete(nodeId);
        } else {
            // Разворачиваем
            childrenContainer.style.display = 'flex';
            if (icon) icon.className = 'bi bi-chevron-up';
            OrgTree.expandedNodes.add(nodeId);
        }
    },
    
    // Развернуть все
    expandAll: () => {
        DomUtils.queryAll('[id^="children-"]').forEach(container => {
            container.style.display = 'flex';
        });
        DomUtils.queryAll('.toggle-icon i').forEach(icon => {
            icon.className = 'bi bi-chevron-up';
        });
        OrgTree.expandedNodes.clear();
    },
    
    // Свернуть все
    collapseAll: () => {
        DomUtils.queryAll('[id^="children-"]').forEach(container => {
            container.style.display = 'none';
        });
        DomUtils.queryAll('.toggle-icon i').forEach(icon => {
            icon.className = 'bi bi-chevron-down';
        });
        OrgTree.expandedNodes.clear();
    }
};

// Управление основными блоками
const MainBlocks = {
    scienceOpen: false,
    organizationOpen: false,
    
    toggleScience: () => {
        const container = DomUtils.get('science-container');
        const icon = DomUtils.query('#science-icon i');
        
        MainBlocks.scienceOpen = !MainBlocks.scienceOpen;
        
        if (MainBlocks.scienceOpen) {
            container.style.display = 'block';
            if (icon) icon.className = 'bi bi-chevron-up';
        } else {
            container.style.display = 'none';
            if (icon) icon.className = 'bi bi-chevron-down';
        }
    },
    
    toggleOrganization: () => {
        const container = DomUtils.get('organization-container');
        const icon = DomUtils.query('#organization-icon i');
        
        MainBlocks.organizationOpen = !MainBlocks.organizationOpen;
        
        if (MainBlocks.organizationOpen) {
            container.style.display = 'block';
            if (icon) icon.className = 'bi bi-chevron-up';
        } else {
            container.style.display = 'none';
            if (icon) icon.className = 'bi bi-chevron-down';
        }
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
    
    // Скрываем все дочерние контейнеры
    DomUtils.queryAll('[id^="children-"]').forEach(container => {
        container.style.display = 'none';
    });
    
    DomUtils.queryAll('[id$="-container"]:not([id^="children-"])').forEach(container => {
        if (container.id !== 'science-container' && container.id !== 'organization-container') {
            container.style.display = 'none';
        }
    });
});

// Экспортируем глобальные объекты
window.OrgTree = OrgTree;
window.MainBlocks = MainBlocks;
window.Staff = Staff;
window.Search = Search;