import axios from "axios";

export const django = axios.create({
  baseURL: import.meta.env.VITE_DJANGO_URL || "http://localhost:8000"
});

export const fastapi = axios.create({
  baseURL: import.meta.env.VITE_FASTAPI_URL || "http://localhost:8001"
});

django.interceptors.request.use((config) => {
  const token = localStorage.getItem("access") || sessionStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

django.interceptors.response.use(
  response => response,
  async error => {
    const request = error.config;
    const requestUrl = request?.url || "";
    if (
      error.response?.status !== 401 ||
      !request ||
      request._retried ||
      requestUrl.includes("/api/auth/login/") ||
      requestUrl.includes("/api/auth/refresh/")
    ) {
      return Promise.reject(error);
    }

    const storage = localStorage.getItem("refresh") ? localStorage : sessionStorage;
    const refresh = storage.getItem("refresh");
    if (!refresh) return Promise.reject(error);

    request._retried = true;
    try {
      const baseURL = django.defaults.baseURL.replace(/\/+$/, "");
      const response = await axios.post(`${baseURL}/api/auth/refresh/`, { refresh });
      storage.setItem("access", response.data.access);
      if (response.data.refresh) storage.setItem("refresh", response.data.refresh);
      request.headers.Authorization = `Bearer ${response.data.access}`;
      return django(request);
    } catch (refreshError) {
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      sessionStorage.removeItem("access");
      sessionStorage.removeItem("refresh");
      return Promise.reject(refreshError);
    }
  }
);
