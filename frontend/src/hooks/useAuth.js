import { useState, useEffect, useCallback } from "react";
import { authService } from "../services/authService";
import toast from "react-hot-toast";

export const useAuth = () => {
    const [user, setUser] = useState(authService.getCurrentUser());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // --- Login ---
    const login = useCallback(async (email, password) => {
        setLoading(true);
        try {
            const loggedInUser = await authService.login(email, password);
            setUser(loggedInUser);
            setError(null);
            toast.success("Logged in successfully");
            return loggedInUser;
        } catch (err) {
            setError(err);
            toast.error("Login failed");
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    // --- Register ---
    const register = useCallback(async (userData) => {
        setLoading(true);
        try {
            const response = await authService.register(userData);
            toast.success("Registration successful");
            return response;
        } catch (err) {
            setError(err);
            toast.error("Registration failed");
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    // --- Logout ---
    const logout = useCallback(() => {
        authService.logout();
        setUser(null);
        toast.success("Logged out");
    }, []);

    // --- Update Profile ---
    const updateProfile = useCallback(async (userData) => {
        setLoading(true);
        try {
            const updatedUser = await authService.updateProfile(userData);
            setUser(updatedUser);
            toast.success("Profile updated");
            return updatedUser;
        } catch (err) {
            setError(err);
            toast.error("Profile update failed");
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    // --- Change Password ---
    const changePassword = useCallback(async (passwords) => {
        setLoading(true);
        try {
            await authService.changePassword(passwords);
            toast.success("Password changed successfully");
        } catch (err) {
            setError(err);
            toast.error("Password change failed");
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    // --- Sync user state on mount ---
    useEffect(() => {
        const currentUser = authService.getCurrentUser();
        if (currentUser) setUser(currentUser);
    }, []);

    return {
        user,
        loading,
        error,
        login,
        register,
        logout,
        updateProfile,
        changePassword,
    };
};