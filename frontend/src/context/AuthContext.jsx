import React, {createContext, useState, useContext, useEffect, Children} from "react";
import { authService } from "../services/auth";
import { create } from "zustand";

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ Children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const currentUser = authService.getCurrentUser();
        setUser(currentUser);
        setLoading(false);
    }, []);

    const login = async(email, password) => {
        const userData = await authService.login(email, password);
        setUser(userData);
        return userData
    }
    
    const logout = () => {
        authService.logout();
        setUser(null);
    }

    const updateUser = (userData) => {
        setUser(userData);
    }

    const value = {
        user,
        login,
        logout,
        updateUser,
        isAuthenticated: !!user,
        loading
    }

    return (
        <AuthContext.Provider value={value}>
            {Children}
        </AuthContext.Provider>
    )
}