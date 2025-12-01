import { tripRecommand } from "../api/recommandApi.js";

export const AVAILABLE_TAGS = ["history", "nature", "food", "culture", "art", "shopping", "adventure"];
export const BLOCK_CONFIG = [
    { id: 'morning', label: 'Buổi Sáng', defaultStart: '08:00', defaultEnd: '11:30', icon: 'fa-sun', iconClass: 'icon-amber', textClass: 'bg-amber' },
    { id: 'lunch', label: 'Buổi Trưa', defaultStart: '11:30', defaultEnd: '13:00', icon: 'fa-utensils', iconClass: 'icon-orange', textClass: 'bg-orange' },
    { id: 'afternoon', label: 'Buổi Chiều', defaultStart: '13:30', defaultEnd: '17:30', icon: 'fa-cloud-sun', iconClass: 'icon-blue', textClass: 'bg-blue' },
    { id: 'dinner', label: 'Buổi Tối', defaultStart: '18:00', defaultEnd: '19:30', icon: 'fa-moon', iconClass: 'icon-indigo', textClass: 'bg-indigo' },
    { id: 'evening', label: 'Về Đêm', defaultStart: '20:00', defaultEnd: '22:00', icon: 'fa-martini-glass', iconClass: 'icon-purple', textClass: 'bg-purple' },
];


export let currentConfig = {
    city: "Hà Nội",
    start_date: new Date().toISOString().split('T')[0],
    num_days: 3,
    preferred_tags: ["history", "food"],
    morning: { enabled: true, start: "08:00", end: "11:30" },
    lunch: { enabled: true, start: "11:30", end: "13:00" },
    afternoon: { enabled: true, start: "13:30", end: "17:30" },
    dinner: { enabled: true, start: "18:00", end: "19:30" },
    evening: { enabled: false, start: "20:00", end: "22:00" }
};

export function updateConfig(newConfig) {
    currentConfig = newConfig;
}
