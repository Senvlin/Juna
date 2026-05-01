import axios from "axios";

const request = axios.create({
  baseURL: "http://127.0.0.1:8080/api",
  timeout: 5000, // 超时时间 5 秒
});

request.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

request.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error("请求失败:", error);
    return Promise.reject(error);
  }
);

export default request;
