import api from './api';

export const authService = {
    login: async (email, password) => {
        const response = await api.post('/auth/login/', {email, password});
        const {access, refresh, user} = response.data;

        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        localStorage.setItem('user', JSON.stringify(user));

        return user;
    },
    
    register: async (userData) =>{
        const response = await api.post('/auth/register/', userData);
        return response.data;
    },

    logout: () => {
        localStorage.clear();
        window.location.href = '/login';
    },

    getCurrentUser: () => {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },

    updateProfile: async (userData) => {
        const response = await api.put('/auth/profile/', userData);
        localStorage.setItem('user', JSON.stringify(response.data));
        return response.data;
    },

    changePassword: async (passwords) => {
        await api.post('/auth/change_password/', passwords);
    }
};