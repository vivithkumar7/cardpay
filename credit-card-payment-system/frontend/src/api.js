import axios from "axios";

let refreshPromise = null;
export const AUTH_EXPIRED_EVENT = "auth:expired";

function clearAuth() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  sessionStorage.removeItem("access");
  sessionStorage.removeItem("refresh");
  window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
}

export const django = axios.create({
  baseURL: import.meta.env.VITE_DJANGO_URL || "http://localhost:8000"
});

export const fastapi = axios.create({
  baseURL: import.meta.env.VITE_FASTAPI_URL || "http://localhost:8001"
});

function getDeviceId() {
  const key = "paysecure_device_id";
  let deviceId = localStorage.getItem(key);
  if (!deviceId && window.crypto?.randomUUID) {
    deviceId = window.crypto.randomUUID();
    localStorage.setItem(key, deviceId);
  }
  return deviceId;
}

fastapi.interceptors.request.use((config) => {
  const deviceId = getDeviceId();
  if (deviceId) config.headers["X-Device-ID"] = deviceId;
  return config;
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
    if (!refresh) {
      clearAuth();
      return Promise.reject(error);
    }

    request._retried = true;
    try {
      const baseURL = django.defaults.baseURL.replace(/\/+$/, "");
      const response = await (
        refreshPromise ||
        (refreshPromise = axios
          .post(`${baseURL}/api/auth/refresh/`, { refresh })
          .finally(() => {
            refreshPromise = null;
          }))
      );
      storage.setItem("access", response.data.access);
      if (response.data.refresh) storage.setItem("refresh", response.data.refresh);
      request.headers.Authorization = `Bearer ${response.data.access}`;
      return django(request);
    } catch (refreshError) {
      clearAuth();
      return Promise.reject(refreshError);
    }
  }
);
